# Vision Optimization Guide

## Overview

The Vision Optimization feature uses AI to enhance your product vision statements, ensuring they generate EXCELLENT quality work items in your Azure DevOps backlog. By incorporating domain-specific context with weighted priorities, the system creates vision statements that lead to more actionable and higher-quality epics, features, and user stories.

## How It Works

### 1. Domain Weighting

When optimizing a vision, you can select up to 3 domains that relate to your product. The system automatically applies intelligent weighting:

- **1 Domain**: 100% focus
- **2 Domains**: Primary (80%), Secondary (20%)
- **3 Domains**: Primary (70%), Secondary (20%), Tertiary (10%)

This weighting ensures your vision emphasizes the most important domain while incorporating relevant aspects from secondary domains.

### 2. Quality Assessment

The Vision Optimizer:
- Evaluates your original vision statement
- Identifies areas for improvement
- Enhances clarity, specificity, and actionability
- Ensures the vision will generate work items with 75+ quality scores

### 3. Optimization Process

The AI agent:
1. Analyzes your original vision
2. Incorporates domain-specific terminology and best practices
3. Structures the vision for optimal work item generation
4. Provides feedback on what was improved

## Using Vision Optimization

### Step 1: Access the Feature

From the welcome screen, click the **"Optimize New Vision"** button (purple with sparkles icon).

### Step 2: Enter Your Vision

1. Paste or type your existing vision statement
2. The system will show a real-time quality check
3. You'll see if it needs optimization (below EXCELLENT rating)

### Step 3: Select Domains

1. Choose 1-3 domains from the grid that best match your product
2. The interface shows the weighting distribution:
   - Primary (first selected)
   - Secondary (if 2+ selected)
   - Tertiary (if 3 selected)

### Step 4: Optimize

1. Click **"Optimize Vision"**
2. The AI will process your vision (typically 10-30 seconds)
3. Review the optimized version and improvement feedback

### Step 5: Next Steps

You have two options:

1. **Save for Later**: Saves the optimized vision to your library
2. **Approve & Create New Backlog**: Immediately starts backlog generation with the optimized vision

## Best Practices

### Writing Initial Visions

Even though the optimizer will enhance your vision, starting with a good foundation helps:

1. **Be Specific**: Include your product's purpose and target users
2. **Set Goals**: Mention key outcomes or benefits
3. **Keep it Concise**: 2-4 sentences is usually ideal

### Domain Selection

1. **Primary Domain**: Choose the domain that best represents your product's core function
2. **Secondary Domain**: Select complementary aspects (e.g., if building an e-commerce platform, primary might be "E-commerce" and secondary "Customer Experience")
3. **Tertiary Domain**: Add only if truly relevant to avoid diluting focus

### When to Optimize

Optimize your vision when:
- Starting a new project
- Your original vision scores below EXCELLENT (80+)
- You want domain-specific enhancements
- Planning a major product pivot

## Examples

### Before Optimization
```
"We want to build a platform that helps small businesses manage their operations better."
```
**Quality Score**: 72/100 (GOOD)

### After Optimization (with E-commerce + Data Analytics domains)
```
"Empower small business owners with an integrated e-commerce operations platform that combines intelligent inventory management, automated order fulfillment, and real-time analytics dashboards. The platform will streamline daily operations through data-driven insights, reducing manual tasks by 60% while providing predictive analytics for demand forecasting and customer behavior patterns."
```
**Quality Score**: 91/100 (EXCELLENT)

### Improvements Made:
- Added specific features (inventory, fulfillment, analytics)
- Quantified benefits (60% reduction)
- Incorporated domain terminology
- Enhanced clarity and actionability

## Managing Optimized Visions

### Viewing Your Library

1. From Project History, click **"Optimized Visions"** tab
2. See all your saved optimized visions
3. View quality scores and domain combinations

### Reusing Visions

1. Click on any saved vision to view details
2. Select **"Create Backlog"** to start a new project
3. The wizard pre-fills with the optimized vision and domains

### Version Management

- The system replaces old optimizations (no version history)
- Each optimization is tied to your user account
- Backlogs track which optimized vision they used

## Troubleshooting

### "Optimization Failed"
- Check your internet connection
- Ensure your LLM provider is configured correctly
- Try selecting fewer domains
- Simplify your initial vision

### Quality Score Still Low
- The vision may be too vague
- Try adding more specific goals or outcomes
- Ensure domains match your product type
- Consider manual editing after optimization

### Domain Selection Issues
- Maximum 3 domains allowed
- Some domain combinations work better together
- If unsure, start with 1-2 domains

## Integration with Backlog Generation

When you create a backlog from an optimized vision:

1. The system uses the enhanced vision for all work item generation
2. Domain context influences epic and feature creation
3. Higher quality visions produce better structured backlogs
4. Reduced need for manual cleanup in Azure DevOps

## Tips for Success

1. **Iterate**: You can optimize multiple versions of your vision
2. **Compare**: Try different domain combinations to see variations
3. **Learn**: Review the optimization feedback to improve future visions
4. **Save Time**: Well-optimized visions reduce backlog cleanup work
5. **Quality First**: Better visions create better work items throughout the hierarchy