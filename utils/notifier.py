import os
import smtplib
import requests
from email.mime.text import MIMEText
from dotenv import load_dotenv
from typing import Dict, Any
from config.config_loader import Config

# Load environment variables once
load_dotenv()

class Notifier:
    def __init__(self, config: Config = None):
        self.config = config
        self.teams_webhook = os.getenv("TEAMS_WEBHOOK_URL")
        self.smtp_server = os.getenv("EMAIL_SMTP_SERVER")
        self.smtp_port = int(os.getenv("EMAIL_SMTP_PORT", 587))
        self.use_tls = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
        self.username = os.getenv("EMAIL_USERNAME")
        self.password = os.getenv("EMAIL_PASSWORD")
        self.email_from = os.getenv("EMAIL_FROM")
        self.email_to = os.getenv("EMAIL_TO")
        
        # Get notification settings from config
        if config:
            notification_settings = config.settings.get('notifications', {})
            self.enabled = notification_settings.get('enabled', True)
            self.channels = notification_settings.get('channels', ['teams', 'email'])
        else:
            self.enabled = True
            self.channels = ['teams', 'email']

    def send_completion_notification(self, workflow_data: Dict[str, Any], stats: Dict[str, Any]):
        """Send workflow completion notification."""
        if not self.enabled:
            print("🔇 Notifications disabled in configuration")
            return
        
        print(f"📢 Sending completion notification - enabled channels: {self.channels}")
        print(f"📊 Statistics received: {stats}")
        print(f"📋 Workflow data keys: {list(workflow_data.keys())}")

        # CRITICAL: Check if this is actually a failure disguised as completion
        total_work_items = (stats.get('epics_generated', 0) + stats.get('features_generated', 0) + 
                           stats.get('user_stories_generated', 0) + stats.get('tasks_generated', 0))
        
        execution_metadata = workflow_data.get('metadata', {}).get('execution_metadata', {})
        errors = execution_metadata.get('errors', [])
        critical_error = execution_metadata.get('critical_error')
        failed_stage = execution_metadata.get('failed_stage')
        
        # Detect quality assessment failures or zero work items
        has_quality_failure = any('quality assessment failed' in str(error).lower() for error in errors)
        has_critical_failure = critical_error is not None
        
        if total_work_items == 0 or has_quality_failure or has_critical_failure:
            print("🚨 DETECTED WORKFLOW FAILURE - Sending error notification instead of completion")
            # This is actually a failure, not a completion
            failure_reason = (
                critical_error or 
                "Quality assessment failed - no EXCELLENT work items generated" if has_quality_failure else
                "Workflow completed but generated zero work items"
            )
            
            self.send_error_notification(
                Exception(failure_reason),
                {
                    'stages_completed': workflow_data.get('metadata', {}).get('stages_completed', []),
                    'start_time': workflow_data.get('metadata', {}).get('execution_metadata', {}).get('start_time'),
                    'failed_stage': failed_stage,
                    'total_errors': len(errors),
                    'domain': workflow_data.get('metadata', {}).get('project_context', {}).get('domain', 'unknown')
                }
            )
            return

        # Get staging summary for upload results
        staging_summary = self._get_staging_summary(workflow_data)

        # --- Persist job to database ---
        backlog_job_id = None
        try:
            from db import add_backlog_job
            # Use the first email in the notification list as user ID
            user_emails = self.config.settings.get('notifications', {}).get('summary_report', {}).get('send_to', [])
            user_email = user_emails[0] if user_emails else 'unknown@unknown.com'
            backlog_job_id = add_backlog_job(
                user_email=user_email,
                project_name=workflow_data.get('metadata', {}).get('project_context', {}).get('project_name', 'Unknown Project'),
                epics_generated=stats.get('epics_generated', 0),
                features_generated=stats.get('features_generated', 0),
                user_stories_generated=stats.get('user_stories_generated', 0),
                tasks_generated=stats.get('tasks_generated', 0),
                test_cases_generated=stats.get('test_cases_generated', 0),
                execution_time_seconds=stats.get('execution_time_seconds'),
                raw_summary={
                    'project_name': workflow_data.get('metadata', {}).get('project_context', {}).get('project_name', 'Unknown Project'),
                    'job_id': workflow_data.get('metadata', {}).get('job_id', ''),
                    'epics_generated': stats.get('epics_generated', 0),
                    'features_generated': stats.get('features_generated', 0),
                    'user_stories_generated': stats.get('user_stories_generated', 0),
                    'tasks_generated': stats.get('tasks_generated', 0),
                    'test_cases_generated': stats.get('test_cases_generated', 0),
                    'execution_time_seconds': stats.get('execution_time_seconds'),
                    'ado_summary': workflow_data.get('azure_integration', {}),
                    'azure_config': workflow_data.get('metadata', {}).get('azure_config', {}),
                    'staging_summary': staging_summary,
                    'created_at': stats.get('created_at'),
                    'test_artifacts_included': workflow_data.get('metadata', {}).get('test_artifacts_included', True)
                }
            )
            print(f"✅ Backlog job logged to database with ID: {backlog_job_id}")
            
            # Generate and save summary report
            if backlog_job_id:
                try:
                    from utils.report_generator import BacklogSummaryReportGenerator
                    from db import db
                    
                    # Get job data from database (we just saved it)
                    job_data = {
                        'id': backlog_job_id,
                        'project_name': workflow_data.get('metadata', {}).get('project_context', {}).get('project_name', 'Unknown Project'),
                        'created_at': stats.get('created_at'),
                        'status': 'completed',
                        'epics_generated': stats.get('epics_generated', 0),
                        'features_generated': stats.get('features_generated', 0),
                        'user_stories_generated': stats.get('user_stories_generated', 0),
                        'tasks_generated': stats.get('tasks_generated', 0),
                        'test_cases_generated': stats.get('test_cases_generated', 0),
                        'execution_time_seconds': stats.get('execution_time_seconds'),
                        'raw_summary': {
                            'project_name': workflow_data.get('metadata', {}).get('project_context', {}).get('project_name', 'Unknown Project'),
                            'job_id': workflow_data.get('metadata', {}).get('job_id', ''),
                            'azure_config': workflow_data.get('metadata', {}).get('azure_config', {}),
                            'staging_summary': staging_summary,
                            'test_artifacts_included': workflow_data.get('metadata', {}).get('test_artifacts_included', True)
                        }
                    }
                    
                    # Get current log content
                    log_content = self._get_current_log_content(workflow_data.get('metadata', {}).get('job_id', ''))
                    
                    # Generate report
                    generator = BacklogSummaryReportGenerator()
                    report_data = generator.generate_report(job_data, log_content)
                    
                    # Save report to database
                    if db.save_backlog_report(backlog_job_id, report_data):
                        print(f"✅ Summary report saved to database for job ID: {backlog_job_id}")
                    else:
                        print(f"⚠️ Failed to save summary report to database for job ID: {backlog_job_id}")
                        
                except Exception as report_exc:
                    print(f"⚠️ Failed to generate/save summary report: {report_exc}")
                    
        except Exception as db_exc:
            print(f"❌ Failed to log backlog job to database: {db_exc}")
        
        # Generate summary message
        project_name = workflow_data.get('metadata', {}).get('project_context', {}).get('project_name', 'Unknown Project')
        
        # Get Azure DevOps information
        azure_config = workflow_data.get('metadata', {}).get('azure_config', {})
        ado_project = azure_config.get('project', 'Not specified')
        ado_area_path = azure_config.get('area_path', 'Not specified')
        
        exec_time = stats.get('execution_time_seconds')
        
        # Format execution time
        if exec_time is not None:
            if exec_time < 60:
                exec_time_str = f"{exec_time:.1f} seconds"
            elif exec_time < 3600:
                minutes = int(exec_time // 60)
                seconds = exec_time % 60
                exec_time_str = f"{minutes}m {seconds:.1f}s"
            else:
                hours = int(exec_time // 3600)
                minutes = int((exec_time % 3600) // 60)
                exec_time_str = f"{hours}h {minutes}m"
        else:
            exec_time_str = "N/A"
        
        # Add warning if any artifacts are missing
        warning = ""
        azure_integration = workflow_data.get('azure_integration', {})
        if azure_integration.get('missing_artifacts'):
            warning = f"\n\n⚠️ *Warning*: The following artifact types were NOT created: {', '.join(azure_integration['missing_artifacts'])}. Please review the logs and agent outputs."
        elif azure_integration.get('warning'):
            warning = f"\n\n⚠️ {azure_integration['warning']}"
        
        # Add warnings from execution metadata
        execution_metadata = workflow_data.get('metadata', {}).get('execution_metadata', {})
        errors = execution_metadata.get('errors', [])
        if errors:
            error_list = "\n".join([f"• {error}" for error in errors])
            warning += f"\n\n⚠️ *Warnings/Issues Encountered:*\n{error_list}"
        
        # Generate upload summary with Azure DevOps details
        upload_summary = self._format_upload_summary(staging_summary, azure_integration)
        
        # Calculate total items generated
        total_generated = (stats.get('epics_generated', 0) + stats.get('features_generated', 0) + 
                          stats.get('user_stories_generated', 0) + stats.get('tasks_generated', 0) + 
                          stats.get('test_cases_generated', 0))
        
        message = f"""
🎉 **Agile Backlog Automation Complete**

**Project:** {project_name}
**Azure DevOps Project:** {ado_project}
**Area Path:** {ado_area_path}

**Generation Summary:**
• Total Work Items: {total_generated}
• Epics: {stats.get('epics_generated', 0)}
• Features: {stats.get('features_generated', 0)}
• User Stories: {stats.get('user_stories_generated', 0)}
• Tasks: {stats.get('tasks_generated', 0)}
• Test Cases: {stats.get('test_cases_generated', 0)}
• Generation Time: {exec_time_str}

**Upload Results:**
{upload_summary}{warning}

{self._get_retry_instructions(staging_summary)}
        """.strip()
        
        success_count = 0
        if 'teams' in self.channels:
            print("📤 Sending Teams notification...")
            try:
                if self.send_teams(message):
                    success_count += 1
                    print("✅ Teams notification sent successfully")
                else:
                    print("❌ Teams notification failed")
            except Exception as e:
                print(f"❌ Teams notification error: {e}")
                
        if 'email' in self.channels:
            print("📧 Sending email notification...")
            try:
                if self.send_email("Backlog Automation Complete", message):
                    success_count += 1
                    print("✅ Email notification sent successfully")
                else:
                    print("❌ Email notification failed")
            except Exception as e:
                print(f"❌ Email notification error: {e}")
                import traceback
                print(f"Email error traceback: {traceback.format_exc()}")
        
        print(f"📊 Notification summary: {success_count}/{len(self.channels)} channels successful")
    
    def send_error_notification(self, error: Exception, metadata: Dict[str, Any]):
        """Send error notification."""
        if not self.enabled:
            return
        
        stages_completed = metadata.get('stages_completed', [])
        failed_stage = metadata.get('failed_stage', 'Unknown')
        domain = metadata.get('domain', 'unknown')
        error_str = str(error)
        
        # Check if this is a quality assessment failure
        is_quality_failure = 'quality assessment failed' in error_str.lower()
        is_domain_issue = 'inadequate llm training' in error_str.lower()
        
        if is_quality_failure:
            message = f"""
❌ **Agile Backlog Automation - Quality Assessment Failed**

**Issue:** Work items failed to meet EXCELLENT quality standards
**Domain:** {domain}
**Failed Stage:** {failed_stage}
**Stages Completed:** {', '.join(stages_completed) if stages_completed else 'None'}

**Root Cause Analysis:**
{error_str}

**Recommended Actions:**
1. **Review Product Vision**: Ensure the vision statement is comprehensive and domain-specific
2. **Check LLM Model**: Consider using a more capable model (e.g., upgrade from 8B to 32B+ parameters)
3. **Domain Expertise**: Verify the model has adequate training for the {domain} domain
4. **Input Quality**: Provide more detailed requirements and context

**What This Means:**
The AI agents could not generate work items that meet professional quality standards. Rather than creating subpar content that would require manual cleanup, the system stopped the workflow to maintain quality standards.
            """.strip()
        else:
            message = f"""
❌ **Agile Backlog Automation Failed**

**Error:** {error_str}
**Failed Stage:** {failed_stage}
**Stages Completed:** {', '.join(stages_completed) if stages_completed else 'None'}
**Time:** {metadata.get('start_time', 'Unknown')}

Please check the logs for more details.
            """.strip()
        
        if 'teams' in self.channels:
            self.send_teams(message)
        if 'email' in self.channels:
            self.send_email("Backlog Automation Failed", message)

    def send_critical_notification(self, notification_data: Dict[str, Any]):
        """Send critical issue notification for high-priority backlog discrepancies."""
        if not self.enabled:
            return
        high_priority_count = notification_data.get('high_priority_count', 0)
        total_discrepancies = notification_data.get('total_discrepancies', 0)
        timestamp = notification_data.get('timestamp', 'Unknown')
        report_summary = notification_data.get('report_summary', {})
        details = ""
        if report_summary:
            details = f"\n\nSummary: {report_summary}"
        message = f"""
🚨 **Critical Backlog Issues Detected**

**High Priority Issues:** {high_priority_count}
**Total Discrepancies:** {total_discrepancies}
**Detection Time:** {timestamp}{details}

**Action Required:** Please review the backlog validation report and address critical issues immediately.

Critical issues may include:
- Missing required work items
- Incomplete hierarchies
- Quality validation failures
- Integration compliance issues

Check the application logs for detailed issue descriptions and remediation steps.
        """.strip()
        if 'teams' in self.channels:
            self.send_teams(message)
        if 'email' in self.channels:
            self.send_email("Critical Backlog Issues Detected", message)

    def send_teams(self, message: str):
        if not self.teams_webhook:
            print("⚠️ Teams webhook not configured.")
            return False

        # Sanitize message for Teams to handle Unicode properly
        sanitized_message = self._sanitize_unicode_for_email(message)
        
        payload = { "text": sanitized_message }
        try:
            # Add timeout to prevent hanging
            response = requests.post(self.teams_webhook, json=payload, timeout=30)
            if response.status_code in [200, 202]:
                print("✅ Teams notification sent.")
                return True
            else:
                print(f"❌ Teams error: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.Timeout:
            print("❌ Teams notification timed out after 30 seconds")
            return False
        except Exception as e:
            print(f"❌ Teams exception: {e}")
            return False

    def send_email(self, subject: str, body: str):
        if not all([self.smtp_server, self.username, self.password, self.email_from, self.email_to]):
            missing_vars = []
            if not self.smtp_server: missing_vars.append("EMAIL_SMTP_SERVER")
            if not self.username: missing_vars.append("EMAIL_USERNAME") 
            if not self.password: missing_vars.append("EMAIL_PASSWORD")
            if not self.email_from: missing_vars.append("EMAIL_FROM")
            if not self.email_to: missing_vars.append("EMAIL_TO")
            print(f"⚠️ Email settings incomplete. Missing: {', '.join(missing_vars)}")
            return False

        # Sanitize subject and body for email to handle Unicode properly
        sanitized_subject = self._sanitize_unicode_for_email(subject)
        sanitized_body = self._sanitize_unicode_for_email(body)

        msg = MIMEText(sanitized_body, 'plain', 'utf-8')
        msg["Subject"] = sanitized_subject
        msg["From"] = self.email_from
        msg["To"] = self.email_to

        try:
            print(f"📧 Attempting to send email via {self.smtp_server}:{self.smtp_port} to {self.email_to}")
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                if self.use_tls:
                    print("🔒 Starting TLS encryption")
                    server.starttls()
                print("🔐 Logging in to SMTP server")
                server.login(self.username, self.password)
                print("📤 Sending email message")
                server.sendmail(self.email_from, [self.email_to], msg.as_string())
                print("✅ Email notification sent successfully.")
                return True
        except smtplib.SMTPException as e:
            print(f"❌ SMTP error: {e}")
            return False
        except ConnectionError as e:
            print(f"❌ Email connection error: {e}")
            return False
        except TimeoutError as e:
            print(f"❌ Email timeout error: {e}")
            return False
        except Exception as e:
            print(f"❌ Email exception: {e}")
            print(f"   SMTP Server: {self.smtp_server}:{self.smtp_port}")
            print(f"   TLS Enabled: {self.use_tls}")
            print(f"   From: {self.email_from}")
            print(f"   To: {self.email_to}")
            return False

    def _sanitize_unicode_for_email(self, text: str) -> str:
        """Sanitize Unicode characters for email compatibility."""
        try:
            import re
            
            # Replace problematic Unicode characters with safe alternatives
            replacements = {
                '✅': '[SUCCESS]',
                '❌': '[FAILED]',
                '⚠️': '[WARNING]',
                '📊': '[STATS]',
                '🔍': '[SEARCH]',
                '📝': '[NOTE]',
                '🎯': '[TARGET]',
                '🚀': '[LAUNCH]',
                '💡': '[IDEA]',
                '🔧': '[TOOL]',
                '📋': '[CHECKLIST]',
                '🎨': '[DESIGN]',
                '🔒': '[SECURE]',
                '🌟': '[STAR]',
                '⭐': '[STAR]',
                '🎉': '[CELEBRATE]',
                '🔄': '[REFRESH]',
                '📈': '[TREND]',
                '💾': '[SAVE]',
                '🎪': '[EVENT]',
                '🚨': '[ALERT]',
                '📧': '[EMAIL]',
                '📤': '[SEND]',
                '📥': '[RECEIVE]'
            }
            
            for unicode_char, replacement in replacements.items():
                text = text.replace(unicode_char, replacement)
            
            # Remove any remaining problematic Unicode characters
            text = re.sub(r'[^\x00-\x7F]+', '?', text)
            
            return text
        except Exception as e:
            # Fallback to UTF-8 with replacement
            try:
                return str(text).encode('utf-8', errors='replace').decode('utf-8')
            except Exception:
                return str(text).encode('ascii', errors='ignore').decode('ascii')
    
    def _get_current_log_content(self, job_id: str) -> str:
        """Get current log file content for report generation."""
        try:
            from pathlib import Path
            import glob
            
            # Try to find log file
            log_patterns = [
                f"logs/backend_*{job_id}*.log",
                f"logs/supervisor_*{job_id}*.log"
            ]
            
            for pattern in log_patterns:
                log_files = glob.glob(pattern)
                if log_files:
                    # Use the most recent file
                    log_file = sorted(log_files, key=lambda x: Path(x).stat().st_mtime, reverse=True)[0]
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
                        
            return ""  # Return empty string if no log found
            
        except Exception as e:
            print(f"⚠️ Failed to read log file: {e}")
            return ""
    
    def _get_staging_summary(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get staging summary from job data."""
        try:
            job_id = workflow_data.get('metadata', {}).get('job_id')
            if not job_id:
                return {}
            
            from models.work_item_staging import WorkItemStaging
            staging = WorkItemStaging()
            return staging.get_staging_summary(job_id)
        except Exception as e:
            print(f"Warning: Could not get staging summary: {e}")
            return {}
    
    def _format_upload_summary(self, staging_summary: Dict[str, Any], azure_integration: Dict[str, Any] = None) -> str:
        """Format upload summary with Azure DevOps details for email notification."""
        if not staging_summary and not azure_integration:
            return "• Upload status: Not available"
        
        summary_lines = []
        
        # Basic staging summary
        if staging_summary:
            by_status = staging_summary.get('by_status', {})
            total_items = staging_summary.get('total_items', 0)
            success_count = by_status.get('success', 0)
            failed_count = by_status.get('failed', 0)
            skipped_count = by_status.get('skipped', 0)
            
            if total_items > 0:
                success_rate = (success_count / total_items) * 100
                summary_lines.append(f"• Successfully Uploaded: {success_count}/{total_items} ({success_rate:.1f}%)")
                
                if failed_count > 0:
                    summary_lines.append(f"• Failed Uploads: {failed_count}")
                
                if skipped_count > 0:
                    summary_lines.append(f"• Skipped (due to parent failures): {skipped_count}")
        
        # Add Azure DevOps work item details if available
        if azure_integration and azure_integration.get('status') == 'success':
            work_items = azure_integration.get('work_items_created', [])
            if work_items:
                summary_lines.append("")  # Add blank line
                summary_lines.append("**Azure DevOps Work Items Created:**")
                
                # Group by type
                items_by_type = {}
                for item in work_items[:20]:  # Show first 20 items
                    item_type = item.get('type', 'Unknown')
                    if item_type not in items_by_type:
                        items_by_type[item_type] = []
                    items_by_type[item_type].append(item)
                
                # Display grouped items
                for item_type in ['Epic', 'Feature', 'User Story', 'Task', 'Test Case']:
                    if item_type in items_by_type:
                        summary_lines.append(f"\n**{item_type}s:**")
                        for item in items_by_type[item_type][:5]:  # Show first 5 of each type
                            title = item.get('title', 'Untitled')
                            url = item.get('url', '#')
                            summary_lines.append(f"• [{title}]({url})")
                        
                        if len(items_by_type[item_type]) > 5:
                            summary_lines.append(f"• ... and {len(items_by_type[item_type]) - 5} more {item_type}s")
                
                if len(work_items) > 20:
                    summary_lines.append(f"\n*Showing first 20 of {len(work_items)} total work items*")
        
        return "\n".join(summary_lines) if summary_lines else "• No items were uploaded"
    
    def _get_retry_instructions(self, staging_summary: Dict[str, Any]) -> str:
        """Generate retry instructions if there are failures."""
        if not staging_summary:
            return ""
        
        by_status = staging_summary.get('by_status', {})
        failed_count = by_status.get('failed', 0)
        job_id = staging_summary.get('job_id', '')
        
        if failed_count == 0:
            return "✅ All items uploaded successfully."
        
        # Get the application URL from config or environment
        app_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        retry_url = f"{app_url}/my-projects"
        
        return f"""
⚠️ **{failed_count} items failed to upload**

**📋 Next Steps:**
1. Open the application: {retry_url}
2. Find your project card in "Project History"
3. Click the orange "Retry Failed Uploads" button

💾 Your generated work items are safely stored and can be retried without regenerating.
        """.strip()