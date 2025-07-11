#!/usr/bin/env python3
"""Test epic and feature description formatting improvements."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.epic_strategist import EpicStrategist
from agents.feature_decomposer_agent import FeatureDecomposerAgent
from config.config_loader import Config

def test_epic_feature_formatting():
    """Test epic and feature description formatting."""
    
    config = Config('config/settings_testing.yaml')
    epic_agent = EpicStrategist(config)
    feature_agent = FeatureDecomposerAgent(config)
    
    print('🧪 Testing Epic and Feature Description Formatting...')
    print('=' * 80)
    
    # Test Epic formatting
    epic_with_unformatted_description = {
        'title': 'Autonomous Ride Booking Platform',
        'description': 'Design and deliver a user-friendly mobile and web platform that enables users to easily book, track, and personalize rides in a fully autonomous, electric fleet. This epic encompasses robust onboarding, real-time ride status, dynamic pricing display, and accessibility features to address diverse user needs and maximize ride convenience. **Business Value:** Accelerates new user adoption, increases ride bookings, and supports the goal to capture 20% urban ride-sharing market share within two years. **Success Criteria:** - 75% of new users complete a booking within their first week - User satisfaction score improves by 20% post-launch (as measured by NPS) - Mobile and web apps achieve accessibility compliance (WCAG 2.1 AA) **Risks:** - Complexity in integrating real-time tracking with autonomous vehicle systems - Ensuring accessibility features meet regulatory standards for diverse users - High initial learning curve leading to user drop-off'
    }
    
    print('📋 EPIC FORMATTING TEST')
    print('-' * 40)
    print('Original epic description:')
    print(epic_with_unformatted_description['description'])
    
    formatted_epic = epic_agent._format_epic(epic_with_unformatted_description)
    
    print('\n' + '=' * 80)
    print('Formatted epic description:')
    print(formatted_epic['description'])
    
    # Test Feature formatting
    feature_with_unformatted_description = {
        'title': 'Seamless Ride Booking and Tracking',
        'description': 'Enables users to seamlessly book autonomous rides via intuitive web and mobile apps. Users can select start/end locations, view estimated arrival times, choose vehicle types, and confirm bookings with dynamic pricing clearly displayed. After booking, users access real-time ride status (vehicle ETA, route visualization, pickup notifications, and live tracking). This feature includes automatic ride progress updates, handling ride delays/cancellations, and integration with mapping APIs for accurate and accessible route info. The interface is optimized to reduce booking friction, increase booking completion rates, and instill confidence in the autonomous ride experience. **Business Value:** Directly drives ride bookings and user engagement through a frictionless, transparent booking and tracking experience, accelerating adoption and improving operational efficiency. **UI/UX Requirements:** - Intuitive, responsive booking flow for both desktop and mobile - Accessibility compliance (WCAG 2.1 AA, including screen reader and color contrast requirements) - Clear, real-time visual and textual updates for ride status - Contextual prompts and notifications for user guidance **Technical Considerations:** - Integration with vehicle control and status APIs for real-time data - Dynamic pricing engine integration - Scalable notification and update system (push, SMS, in-app) - Secure handling of location and personal data **Dependencies:** - Autonomous vehicle fleet API availability - Accurate real-time mapping/location services'
    }
    
    print('\n\n📋 FEATURE FORMATTING TEST')
    print('-' * 40)
    print('Original feature description:')
    print(feature_with_unformatted_description['description'])
    
    formatted_description = feature_agent._format_feature_description(feature_with_unformatted_description['description'])
    
    print('\n' + '=' * 80)
    print('Formatted feature description:')
    print(formatted_description)
    
    print('\n✅ Epic and Feature formatting test completed!')

if __name__ == "__main__":
    test_epic_feature_formatting()
