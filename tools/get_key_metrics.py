#!/usr/bin/env python3
"""
Key Metrics Collection Script
Gathers comprehensive metrics about the Agile Backlog Automation project.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from utils.safe_logger import get_safe_logger, safe_print
    logger = get_safe_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    def safe_print(msg):
        print(str(msg).encode('ascii', errors='replace').decode('ascii'))

class MetricsCollector:
    """Collects comprehensive project metrics."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.metrics = {}
    
    def count_files_by_extension(self) -> Dict[str, int]:
        """Count files by extension."""
        extensions = {}
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in [
                '.git', '__pycache__', 'node_modules', '.vscode', 
                '.venv', 'venv', 'env', 'site-packages', 'Lib',
                '.pytest_cache', 'build', 'dist'
            ]]
            
            for file in files:
                ext = Path(file).suffix.lower()
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1
                else:
                    extensions['no_extension'] = extensions.get('no_extension', 0) + 1
        
        return extensions
    
    def count_lines_of_code(self) -> Dict[str, int]:
        """Count lines of code by language."""
        line_counts = {}
        
        # Define language extensions
        languages = {
            '.py': 'Python',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript React',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript React',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.json': 'JSON',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.md': 'Markdown',
            '.txt': 'Text',
            '.sql': 'SQL',
            '.bat': 'Batch',
            '.ps1': 'PowerShell'
        }
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in [
                '.git', '__pycache__', 'node_modules', '.vscode', 
                '.venv', 'venv', 'env', 'site-packages', 'Lib',
                '.pytest_cache', 'build', 'dist'
            ]]
            
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in languages:
                    lang = languages[ext]
                    file_path = Path(root) / file
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = len(f.readlines())
                            line_counts[lang] = line_counts.get(lang, 0) + lines
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")
        
        return line_counts
    
    def count_api_endpoints(self) -> Dict[str, Any]:
        """Count API endpoints from the main server file."""
        api_file = self.project_root / "unified_api_server.py"
        endpoints = []
        
        if api_file.exists():
            try:
                with open(api_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find all FastAPI route decorators
                route_pattern = r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
                matches = re.findall(route_pattern, content)
                
                for method, path in matches:
                    endpoints.append({
                        'method': method.upper(),
                        'path': path,
                        'full_path': f"{method.upper()} {path}"
                    })
                
            except Exception as e:
                logger.warning(f"Could not parse API endpoints: {e}")
        
        return {
            'total_endpoints': len(endpoints),
            'endpoints': endpoints
        }
    
    def count_ai_agents(self) -> Dict[str, Any]:
        """Count AI agents and their types."""
        agents_dir = self.project_root / "agents"
        agents = []
        
        if agents_dir.exists():
            for file in agents_dir.glob("*.py"):
                if file.name != "__init__.py":
                    agents.append(file.stem)
        
        qa_agents_dir = agents_dir / "qa"
        qa_agents = []
        if qa_agents_dir.exists():
            for file in qa_agents_dir.glob("*.py"):
                if file.name != "__init__.py":
                    qa_agents.append(file.stem)
        
        return {
            'total_agents': len(agents) + len(qa_agents),
            'main_agents': agents,
            'qa_agents': qa_agents,
            'all_agents': agents + qa_agents
        }
    
    def count_testing_tools(self) -> Dict[str, Any]:
        """Count testing and diagnostic tools."""
        tools_dir = self.project_root / "tools"
        tools = []
        
        if tools_dir.exists():
            for file in tools_dir.glob("*.py"):
                tools.append(file.stem)
        
        return {
            'total_tools': len(tools),
            'tools': tools
        }
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information."""
        db_files = []
        db_size = 0
        
        for db_file in self.project_root.glob("*.db"):
            try:
                size = db_file.stat().st_size
                db_files.append({
                    'name': db_file.name,
                    'size_bytes': size,
                    'size_mb': round(size / (1024 * 1024), 2)
                })
                db_size += size
            except Exception as e:
                logger.warning(f"Could not get info for {db_file}: {e}")
        
        return {
            'total_size_bytes': db_size,
            'total_size_mb': round(db_size / (1024 * 1024), 2),
            'databases': db_files
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        status = {
            'python_version': sys.version,
            'platform': sys.platform,
            'project_root': str(self.project_root),
            'current_directory': os.getcwd()
        }
        
        # Check if key files exist
        key_files = [
            'unified_api_server.py',
            'supervisor/supervisor.py',
            'agents/base_agent.py',
            'utils/prompt_manager.py',
            'frontend/package.json'
        ]
        
        status['key_files_exist'] = {}
        for file_path in key_files:
            full_path = self.project_root / file_path
            status['key_files_exist'][file_path] = full_path.exists()
        
        return status
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all metrics."""
        safe_print("Collecting project metrics...")
        
        self.metrics = {
            'file_counts': self.count_files_by_extension(),
            'line_counts': self.count_lines_of_code(),
            'api_endpoints': self.count_api_endpoints(),
            'ai_agents': self.count_ai_agents(),
            'testing_tools': self.count_testing_tools(),
            'database_info': self.get_database_info(),
            'system_status': self.get_system_status()
        }
        
        return self.metrics
    
    def print_summary(self):
        """Print a formatted summary of metrics."""
        safe_print("\n" + "="*60)
        safe_print("AGILE BACKLOG AUTOMATION - KEY METRICS")
        safe_print("="*60)
        
        # File counts
        safe_print(f"\n[FILES] Total files by extension:")
        for ext, count in sorted(self.metrics['file_counts'].items(), key=lambda x: x[1], reverse=True):
            safe_print(f"  {ext}: {count}")
        
        # Line counts
        safe_print(f"\n[CODE] Lines of code by language:")
        total_lines = 0
        for lang, lines in sorted(self.metrics['line_counts'].items(), key=lambda x: x[1], reverse=True):
            safe_print(f"  {lang}: {lines:,} lines")
            total_lines += lines
        safe_print(f"  TOTAL: {total_lines:,} lines")
        
        # API endpoints
        api_info = self.metrics['api_endpoints']
        safe_print(f"\n[API] Endpoints: {api_info['total_endpoints']}")
        
        # AI agents
        agents_info = self.metrics['ai_agents']
        safe_print(f"\n[AI] Agents: {agents_info['total_agents']}")
        safe_print(f"  Main agents: {len(agents_info['main_agents'])}")
        safe_print(f"  QA agents: {len(agents_info['qa_agents'])}")
        
        # Testing tools
        tools_info = self.metrics['testing_tools']
        safe_print(f"\n[TOOLS] Testing/Diagnostic tools: {tools_info['total_tools']}")
        
        # Database info
        db_info = self.metrics['database_info']
        safe_print(f"\n[DATABASE] Total size: {db_info['total_size_mb']} MB")
        for db in db_info['databases']:
            safe_print(f"  {db['name']}: {db['size_mb']} MB")
        
        # System status
        sys_status = self.metrics['system_status']
        safe_print(f"\n[SYSTEM] Python: {sys_status['python_version'].split()[0]}")
        safe_print(f"  Platform: {sys_status['platform']}")
        
        # Key files status
        safe_print(f"\n[STATUS] Key files:")
        for file_path, exists in sys_status['key_files_exist'].items():
            status = "[SUCCESS]" if exists else "[ERROR]"
            safe_print(f"  {status} {file_path}")
        
        safe_print("\n" + "="*60)
    
    def save_metrics(self, filename: str = "project_metrics.json"):
        """Save metrics to JSON file."""
        output_path = self.project_root / filename
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.metrics, f, indent=2, default=str)
            safe_print(f"[SUCCESS] Metrics saved to: {output_path}")
        except Exception as e:
            safe_print(f"[ERROR] Could not save metrics: {e}")

def main():
    """Main function to collect and display metrics."""
    collector = MetricsCollector()
    metrics = collector.collect_all_metrics()
    collector.print_summary()
    collector.save_metrics()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

