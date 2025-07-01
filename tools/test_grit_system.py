import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supervisor.supervisor import WorkflowSupervisor
from config.config_loader import Config
import yaml
import json
from datetime import datetime

def test_grit_system_pipeline():
    """Test complete pipeline with GRIT (Global Real-Time Inventory Tracking) system."""
    
    print("📦 Testing GRIT System - Complete Pipeline")
    print("=" * 60)
    
    # Load GRIT vision
    with open('samples/grit_vision.yaml', 'r') as f:
        vision_data = yaml.safe_load(f)['grit_vision']
    
    print(f"📋 Product: {vision_data['title']}")
    print(f"🎯 Vision: {vision_data['vision'][:120]}...")
    print(f"🚚 Domain: {vision_data['domain']}")
    print(f"👥 Target Users: {', '.join(vision_data['target_users'][:4])}...")
    print(f"💡 Key Value Props:")
    for i, prop in enumerate(vision_data['value_propositions'][:3], 1):
        print(f"   {i}. {prop}")
    
    # Create vision string for the pipeline
    vision_text = f"""
{vision_data['vision']}

Key Features:
{chr(10).join(f"- {feature}" for feature in vision_data['key_features'])}

Target Users: {', '.join(vision_data['target_users'])}

Business Value:
{vision_data['competitive_advantage']}
"""
    
    # Initialize supervisor
    supervisor = WorkflowSupervisor()
    
    print(f"\n🚀 Starting GRIT Pipeline Execution...")
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔧 Workflow: Epic Strategist → Feature Decomposer → Developer Agent → QA Tester")
    
    try:
        # Configure project context
        print(f"\n⚙️ Configuring Project Context...")
        supervisor.configure_project_context('shipping_logistics', {
            'domain': vision_data['domain'],
            'project_name': vision_data['title'],
            'methodology': vision_data['methodology'],
            'target_users': ', '.join(vision_data['target_users']),
            'platform': vision_data['platform'],
            'team_velocity': '30-40 points per sprint'
        })
        print("✅ Project context configured")
        
        # Run the complete pipeline
        print(f"\n⏳ Processing... (this may take 2-3 minutes)")
        results = supervisor.execute_workflow(
            product_vision=vision_text,
            human_review=False,
            save_outputs=True,
            integrate_azure=True  # This will create work items in ADO
        )
        
        print(f"\n✅ GRIT Pipeline Completed Successfully!")
        
        # Analyze and display results
        if results:
            print(f"\n📊 GRIT System Backlog Analysis:")
            print("=" * 50)
            
            # Count work items by type
            epic_count = len(results.get('epics', []))
            total_features = 0
            total_user_stories = 0
            total_tasks = 0
            total_test_cases = 0
            total_story_points = 0
            total_effort_hours = 0
            
            for epic in results.get('epics', []):
                features = epic.get('features', [])
                total_features += len(features)
                
                for feature in features:
                    user_stories = feature.get('user_stories', [])
                    total_user_stories += len(user_stories)
                    
                    # Count test cases for this feature
                    total_test_cases += len(feature.get('test_cases', []))
                    
                    for story in user_stories:
                        # Count tasks for this user story
                        tasks = story.get('tasks', [])
                        total_tasks += len(tasks)
                        
                        # Sum story points
                        story_points = story.get('story_points', 0)
                        if isinstance(story_points, (int, float)):
                            total_story_points += story_points
                            
                        # Sum effort hours from tasks
                        for task in tasks:
                            effort = task.get('effort_hours', 0)
                            if isinstance(effort, (int, float)):
                                total_effort_hours += effort
            
            print(f"📈 Work Item Summary:")
            print(f"   🎯 Epics: {epic_count}")
            print(f"   🔧 Features: {total_features}")
            print(f"   📝 User Stories: {total_user_stories}")
            print(f"   ⚙️ Tasks: {total_tasks}")
            print(f"   🧪 Test Cases: {total_test_cases}")
            print(f"   📊 Total Work Items: {epic_count + total_features + total_user_stories + total_tasks + total_test_cases}")
            print(f"   🏆 Total Story Points: {total_story_points}")
            print(f"   ⏱️ Total Effort Hours: {total_effort_hours}")
            
            # Display detailed breakdown
            print(f"\n🎯 Epic Breakdown:")
            for i, epic in enumerate(results.get('epics', []), 1):
                print(f"\n📋 Epic {i}: {epic.get('title', 'N/A')}")
                print(f"   💼 Business Value: {epic.get('business_value', 'N/A')[:100]}...")
                print(f"   ⭐ Priority: {epic.get('priority', 'N/A')}")
                
                features = epic.get('features', [])
                print(f"   🔧 Features ({len(features)}):")
                
                for j, feature in enumerate(features[:3], 1):  # Show first 3 features
                    print(f"      {j}. {feature.get('title', 'N/A')}")
                    print(f"         📝 User Stories: {len(feature.get('user_stories', []))}")
                    print(f"         🧪 Test Cases: {len(feature.get('test_cases', []))}")
                    
                    # Show sample user story
                    if feature.get('user_stories'):
                        sample_story = feature['user_stories'][0]
                        print(f"         📖 Sample Story: \"{sample_story.get('user_story', 'N/A')[:80]}...\"")
                        print(f"         🏆 Story Points: {sample_story.get('story_points', 'N/A')}")
                
                if len(features) > 3:
                    print(f"      ... and {len(features) - 3} more features")
            
            # Show test case quality
            print(f"\n🧪 Test Case Quality Analysis:")
            test_types = {}
            risk_levels = {}
            
            for epic in results.get('epics', []):
                for feature in epic.get('features', []):
                    for test_case in feature.get('test_cases', []):
                        test_type = test_case.get('type', 'unknown')
                        risk_level = test_case.get('risk_level', 'unknown')
                        
                        test_types[test_type] = test_types.get(test_type, 0) + 1
                        risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
            
            if test_types:
                print(f"   📊 Test Types: {dict(test_types)}")
                print(f"   ⚠️ Risk Levels: {dict(risk_levels)}")
            
            # Save results with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"output/grit_system_backlog_{timestamp}.json"
            yaml_file = f"output/grit_system_backlog_{timestamp}.yaml"
            
            # Save JSON
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Save YAML for readability
            with open(yaml_file, 'w') as f:
                yaml.dump(results, f, default_flow_style=False, indent=2)
            
            print(f"\n💾 Results saved:")
            print(f"   📄 JSON: {output_file}")
            print(f"   📋 YAML: {yaml_file}")
            
            # Estimate timeline
            sprints_needed = max(1, total_story_points // 40)  # Assuming 40 points per sprint
            print(f"\n⏱️ Development Estimates:")
            print(f"   🏃‍♂️ Estimated Sprints: {sprints_needed} (based on {total_story_points} story points)")
            print(f"   📅 Estimated Timeline: {sprints_needed * 2} weeks (2-week sprints)")
            print(f"   👥 Team Size Recommendation: 5-7 developers + 2 QA + 1 PO")
            
            return results
            
        else:
            print("❌ No results generated - check logs for errors")
            return None
            
    except Exception as e:
        print(f"❌ GRIT Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_grit_vision():
    """Analyze the GRIT vision for completeness and quality."""
    
    print("\n📋 GRIT Vision Analysis")
    print("=" * 40)
    
    try:
        with open('samples/grit_vision.yaml', 'r') as f:
            vision = yaml.safe_load(f)['grit_vision']
        
        print(f"✅ Vision Components:")
        components = [
            'title', 'vision', 'target_users', 'key_features', 
            'value_propositions', 'competitive_advantage', 'success_metrics'
        ]
        
        for component in components:
            if component in vision:
                if component == 'key_features':
                    print(f"   ✅ {component}: {len(vision[component])} features defined")
                elif component == 'target_users':
                    print(f"   ✅ {component}: {len(vision[component])} user types")
                elif component == 'value_propositions':
                    print(f"   ✅ {component}: {len(vision[component])} value props")
                else:
                    print(f"   ✅ {component}: Defined")
            else:
                print(f"   ❌ {component}: Missing")
        
        print(f"\n🎯 Vision Quality Score: {len([c for c in components if c in vision])}/{len(components)} (Excellent!)")
        
    except Exception as e:
        print(f"❌ Error analyzing vision: {e}")

if __name__ == "__main__":
    print("📦 GRIT System - Pipeline Testing")
    print("=" * 50)
    
    # First analyze the vision
    analyze_grit_vision()
    
    # Then run the complete pipeline
    results = test_grit_system_pipeline()
    
    if results:
        print(f"\n🎉 SUCCESS: GRIT System backlog generated successfully!")
        print(f"🚀 Ready for Azure DevOps work item creation!")
        print(f"📈 Houston O&G logistics clients will love this!")
    else:
        print(f"\n❌ FAILED: Check logs and retry")
