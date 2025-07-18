#!/usr/bin/env python3
"""
Test script for TemplateManager - BTS Name & ID replacement functionality
"""

import os
import sys
from modules.template_manager import TemplateManager

def test_extract_bts_info():
    """Test BTS info extraction from template file"""
    print("🔍 Testing BTS Info Extraction...")
    
    template_path = "example_files/5G-S3-AHEGA.xml"
    manager = TemplateManager()
    
    try:
        bts_info = manager.extract_bts_info(template_path)
        
        print("✅ BTS Info Extracted:")
        print(f"   📍 BTS Name: {bts_info['bts_name']}")
        print(f"   🔢 BTS ID: {bts_info['bts_id']}")
        print(f"   📝 BTS Name (dash): {bts_info['bts_name_dash']}")
        print(f"   🏷️  Dist Name: {bts_info['dist_name']}")
        
        return bts_info
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_template_analysis():
    """Test template compatibility analysis"""
    print("\n🔍 Testing Template Analysis...")
    
    template_path = "example_files/5G-S3-AHEGA.xml"
    manager = TemplateManager()
    
    try:
        analysis = manager.analyze_template_compatibility(template_path)
        
        print("✅ Template Analysis:")
        print(f"   📡 Sectors: {analysis['sectors']}")
        print(f"   📻 Has 2G: {analysis['has_2g']}")
        print(f"   📱 Has 3G: {analysis['has_3g']}")
        print(f"   📶 Has 4G: {analysis['has_4g']}")
        print(f"   🔧 RRH Type: {analysis['rrh_type']}")
        print(f"   📋 Recommended Templates: {analysis['recommended_templates']}")
        
        return analysis
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_template_replacement():
    """Test BTS parameter replacement in template"""
    print("\n🔧 Testing Template Replacement...")
    
    # Use template as source to simulate real scenario
    source_template = "example_files/5G-S3-AHEGA.xml"
    target_template = "example_files/5G-no2G-S2-AHEGA.xml"  # Different template to test replacement
    output_path = "generated/test_replaced_template.xml"
    
    manager = TemplateManager()
    
    try:
        # Extract BTS info from source template (simulating real BTS config)
        bts_info = manager.extract_bts_info(source_template)
        
        # Modify BTS info to simulate different station
        test_bts_info = {
            'bts_name': 'TEST_KHILIANI_HOUSE',
            'bts_id': '88888',
            'bts_name_dash': 'TEST-KHILIANI-HOUSE',
            'dist_name': 'MRBTS-88888'
        }
        
        print(f"📋 Using Test BTS Info:")
        print(f"   📍 BTS Name: {test_bts_info['bts_name']}")
        print(f"   🔢 BTS ID: {test_bts_info['bts_id']}")
        
        # Replace parameters in target template
        os.makedirs("generated", exist_ok=True)
        result_path = manager.replace_bts_parameters_in_template(
            target_template, test_bts_info, output_path
        )
        
        print(f"✅ Template replacement completed!")
        print(f"   📄 Output: {result_path}")
        
        # Validate the replacement
        validation = manager.validate_template_replacement(target_template, result_path)
        
        print("🔍 Validation Results:")
        print(f"   ✅ Valid XML: {validation['valid_xml']}")
        print(f"   🏗️  Structure Preserved: {validation['structure_preserved']}")
        print(f"   📝 BTS Name Replaced: {validation['bts_name_replaced']}")
        print(f"   🔢 BTS ID Replaced: {validation['bts_id_replaced']}")
        
        if validation['errors']:
            print(f"   ⚠️  Errors: {validation['errors']}")
        
        return result_path
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def main():
    """Run all tests"""
    print("🚀 Starting TemplateManager Tests...\n")
    
    # Test 1: Extract BTS Info
    bts_info = test_extract_bts_info()
    
    # Test 2: Template Analysis  
    analysis = test_template_analysis()
    
    # Test 3: Template Replacement
    result_path = test_template_replacement()
    
    print("\n" + "="*50)
    print("📊 Test Summary:")
    print("="*50)
    
    if bts_info:
        print("✅ BTS Info Extraction: PASSED")
    else:
        print("❌ BTS Info Extraction: FAILED")
    
    if analysis:
        print("✅ Template Analysis: PASSED")
    else:
        print("❌ Template Analysis: FAILED")
    
    if result_path:
        print("✅ Template Replacement: PASSED")
        print(f"   📁 Generated file: {result_path}")
    else:
        print("❌ Template Replacement: FAILED")
    
    print("\n🎉 Testing completed!")

if __name__ == "__main__":
    main() 