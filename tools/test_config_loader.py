from config.config_loader import Config

def test_config():
    config = Config()

    print("🔧 Environment Variables:")
    for key, value in config.env.items():
        print(f"{key}: {value}")

    print("\n📁 Project Paths:")
    print(config.get_project_paths())

    print("\n🧠 Workflow Sequence:")
    print(config.get_workflow_sequence())

    print("\n📄 Prompt Paths:")
    for agent in config.get_workflow_sequence():
        path = config.get_agent_prompt_path(agent)
        print(f"{agent}: {path}")

    print("\n🔔 Notification Settings:")
    print(config.get_notification_settings())

if __name__ == "__main__":
    test_config()