import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supervisor.supervisor import Supervisor
from config.config_loader import Config
import yaml
import json
from datetime import datetime

def test_complete_oil_gas_pipeline():
    """Test complete pipeline with Oil & Gas domain product vision."""
    
    print("🛢️ Testing Complete Oil & Gas Pipeline")
    print("=" * 60)
    
    # Load Oil & Gas vision
    with open('samples/oil_gas_visions.yaml', 'r') as f:
        visions = yaml.safe_load(f)
    
    # Select drilling operations platform for testing
    vision_data = visions['oil_gas_visions']['drilling_operations_platform']
    
    print(f"📋 Product Vision: {vision_data['title']}")
    print(f"🎯 Vision: {vision_data['vision'][:100]}...")
    print(f"🏭 Domain: {vision_data['domain']}")
    print(f"👥 Target Users: {', '.join(vision_data['target_users'][:3])}...")
    
    # Create test vision input
    test_vision = {
        "project_name": vision_data['title'],
        "domain": vision_data['domain'],
        "methodology": vision_data.get('methodology', 'Agile'),
        "target_users": vision_data['target_users'],
        "platform": vision_data.get('platform', 'web_and_mobile'),
        "description": vision_data['vision'],
        "key_features": vision_data['key_features']
    }
    
    # Initialize supervisor
    config = Config()
    supervisor = Supervisor(config)
    
    print(f"\n🚀 Starting Pipeline Execution...")
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run the complete pipeline
        results = supervisor.run_pipeline(test_vision)
        
        print(f"\n✅ Pipeline Completed Successfully!")
        
        # Analyze results
        if results:
            print(f"\n📊 Results Summary:")
            
            # Count work items
            epic_count = len(results.get('epics', []))
            feature_count = sum(len(epic.get('features', [])) for epic in results.get('epics', []))
            user_story_count = sum(
                len(feature.get('user_stories', [])) 
                for epic in results.get('epics', []) 
                for feature in epic.get('features', [])
            )
            task_count = sum(
                len(story.get('tasks', [])) 
                for epic in results.get('epics', []) 
                for feature in epic.get('features', [])
                for story in feature.get('user_stories', [])
            )
            test_case_count = sum(
                len(feature.get('test_cases', [])) 
                for epic in results.get('epics', []) 
                for feature in epic.get('features', [])
            )
            
            print(f"   📈 Epics: {epic_count}")
            print(f"   🎯 Features: {feature_count}")
            print(f"   📝 User Stories: {user_story_count}")
            print(f"   ⚙️ Tasks: {task_count}")
            print(f"   🧪 Test Cases: {test_case_count}")
            print(f"   📊 Total Work Items: {epic_count + feature_count + user_story_count + task_count + test_case_count}")
            
            # Show sample epic
            if results.get('epics'):
                sample_epic = results['epics'][0]
                print(f"\n📋 Sample Epic:")
                print(f"   Title: {sample_epic.get('title', 'N/A')}")
                print(f"   Business Value: {sample_epic.get('business_value', 'N/A')[:100]}...")
                
                if sample_epic.get('features'):
                    sample_feature = sample_epic['features'][0]
                    print(f"\n🎯 Sample Feature:")
                    print(f"   Title: {sample_feature.get('title', 'N/A')}")
                    print(f"   Description: {sample_feature.get('description', 'N/A')[:100]}...")
                    
                    if sample_feature.get('user_stories'):
                        sample_story = sample_feature['user_stories'][0]
                        print(f"\n📝 Sample User Story:")
                        print(f"   Title: {sample_story.get('title', 'N/A')}")
                        print(f"   Story: {sample_story.get('user_story', 'N/A')}")
                        print(f"   Story Points: {sample_story.get('story_points', 'N/A')}")
                        
                        if sample_story.get('tasks'):
                            sample_task = sample_story['tasks'][0]
                            print(f"\n⚙️ Sample Task:")
                            print(f"   Title: {sample_task.get('title', 'N/A')}")
                            print(f"   Effort Hours: {sample_task.get('effort_hours', 'N/A')}")
                    
                    if sample_feature.get('test_cases'):
                        sample_test = sample_feature['test_cases'][0]
                        print(f"\n🧪 Sample Test Case:")
                        print(f"   Title: {sample_test.get('title', 'N/A')}")
                        print(f"   Type: {sample_test.get('type', 'N/A')}")
                        print(f"   Priority: {sample_test.get('priority', 'N/A')}")
            
            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"output/oil_gas_backlog_{timestamp}.json"
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n💾 Results saved to: {output_file}")
            
            return results
            
        else:
            print("❌ No results generated")
            return None
            
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_shipping_logistics_pipeline():
    """Test complete pipeline with Shipping & Logistics domain."""
    
    print("\n🚢 Testing Complete Shipping & Logistics Pipeline")
    print("=" * 60)
    
    # Load Shipping & Logistics vision
    with open('samples/shipping_logistics_visions.yaml', 'r') as f:
        visions = yaml.safe_load(f)
    
    # Select freight marketplace for testing
    vision_data = visions['shipping_logistics_visions']['freight_marketplace']
    
    print(f"📋 Product Vision: {vision_data['title']}")
    print(f"🎯 Vision: {vision_data['vision'][:100]}...")
    print(f"🚚 Domain: {vision_data['domain']}")
    print(f"👥 Target Users: {', '.join(vision_data['target_users'][:3])}...")
    
    # Create test vision input
    test_vision = {
        "project_name": vision_data['title'],
        "domain": vision_data['domain'],
        "methodology": vision_data.get('methodology', 'Agile'),
        "target_users": vision_data['target_users'],
        "platform": vision_data.get('platform', 'web_and_mobile'),
        "description": vision_data['vision'],
        "key_features": vision_data['key_features']
    }
    
    # Initialize supervisor
    config = Config()
    supervisor = Supervisor(config)
    
    print(f"\n🚀 Starting Pipeline Execution...")
    
    try:
        # Run the complete pipeline
        results = supervisor.run_pipeline(test_vision)
        
        if results:
            print(f"✅ Shipping & Logistics Pipeline Completed!")
            
            # Quick summary
            epic_count = len(results.get('epics', []))
            feature_count = sum(len(epic.get('features', [])) for epic in results.get('epics', []))
            
            print(f"📊 Generated {epic_count} epics with {feature_count} features")
            
            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"output/shipping_logistics_backlog_{timestamp}.json"
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"💾 Results saved to: {output_file}")
            
            return results
        else:
            print("❌ No results generated")
            return None
            
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        return None

if __name__ == "__main__":
    print("🎯 Domain Expansion Testing - Oil & Gas and Shipping & Logistics")
    print("=" * 80)
    
    # Test Oil & Gas domain
    oil_gas_results = test_complete_oil_gas_pipeline()
    
    # Test Shipping & Logistics domain  
    shipping_results = test_shipping_logistics_pipeline()
    
    print("\n🏆 Domain Expansion Testing Complete!")
    print("=" * 80)
    
    if oil_gas_results and shipping_results:
        print("✅ Both new domains working successfully!")
        print("🎯 Ready for Houston O&G clients!")
    elif oil_gas_results:
        print("✅ Oil & Gas domain working!")
        print("⚠️ Shipping & Logistics needs attention")
    elif shipping_results:
        print("✅ Shipping & Logistics domain working!")
        print("⚠️ Oil & Gas needs attention")
    else:
        print("❌ Both domains need troubleshooting")
