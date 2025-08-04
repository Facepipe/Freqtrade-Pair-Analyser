# FILENAME: fix_pairlist_methods.py
# ACTION: CREATE NEW FILE
# DESCRIPTION: Quick fix to add missing methods to pairlist_generator.py

#!/usr/bin/env python3
"""
Fix missing methods in pairlist_generator.py
"""
import re
from pathlib import Path

def fix_pairlist_generator():
    """Fix the pairlist generator file"""
    file_path = Path("pairlist_generator.py")
    
    if not file_path.exists():
        print("❌ pairlist_generator.py not found")
        return False
    
    print("🔧 Fixing pairlist_generator.py...")
    
    # Read the current file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if generate_all_pairlists method exists
    if "def generate_all_pairlists(self)" in content:
        print("✅ generate_all_pairlists method already exists")
        return True
    
    # Find where to insert the method (after generate_stable_pairlist)
    stable_method_end = content.find("        return config", content.find("def generate_stable_pairlist"))
    
    if stable_method_end == -1:
        print("❌ Could not find insertion point")
        return False
    
    # The method to insert
    method_to_insert = '''
    
    def generate_all_pairlists(self):
        """Generate all types of pairlists including comprehensive ALL pairs list"""
        logger.info(f"🚀 Generating all pairlist types for {self.quote_currency}")
        
        generators = [
            ("ALL Exchange Pairs", lambda: self.generate_all_pairs_pairlist(min_volume=0.001)),
            ("High Volume", lambda: self.generate_high_volume_pairlist(min_volume=1000, max_pairs=200)),
            ("Price Filtered", lambda: self.generate_price_filtered_pairlist(min_price=0.00000100, low_price_ratio=0.01)),
            ("Analysis Based", lambda: self.generate_analysis_based_pairlist(top_n=50, min_score=0.3)),
            ("Diversified", lambda: self.generate_diversified_pairlist()),
            ("Stable", lambda: self.generate_stable_pairlist(max_volatility=0.5, min_volume=500))
        ]
        
        generated_files = []
        
        for name, generator in generators:
            try:
                logger.info(f"\\n📋 Generating {name} pairlist...")
                config = generator()
                
                if config and config.get('whitelist_count', 0) > 0:
                    # Create descriptive filename
                    if name == "ALL Exchange Pairs":
                        filename = f"pairsALL_{self.quote_currency.upper()}.json"
                    else:
                        filename = f"pairs{config['config_name'].upper()}.json"
                    
                    output_path = self.save_pairlist(config, filename)
                    if output_path:
                        generated_files.append(output_path)
                else:
                    logger.warning(f"❌ Failed to generate {name} pairlist")
                    
            except Exception as e:
                logger.error(f"❌ Error generating {name} pairlist: {e}")
        
        return generated_files'''
    
    # Insert the method
    insertion_point = stable_method_end + len("        return config")
    new_content = content[:insertion_point] + method_to_insert + content[insertion_point:]
    
    # Write back the file
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print("✅ Added generate_all_pairlists method")
    return True

def test_fix():
    """Test that the fix worked"""
    print("🧪 Testing the fix...")
    
    try:
        import sys
        sys.path.insert(0, '.')
        from pairlist_generator import PairlistGenerator
        
        # Test that the method exists
        generator = PairlistGenerator(quote_currency='USDT')
        
        if hasattr(generator, 'generate_all_pairlists'):
            print("✅ generate_all_pairlists method exists")
        else:
            print("❌ generate_all_pairlists method still missing")
            return False
        
        if hasattr(generator, 'generate_all_pairs_pairlist'):
            print("✅ generate_all_pairs_pairlist method exists")
        else:
            print("❌ generate_all_pairs_pairlist method missing")
            return False
        
        print("✅ All methods present")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main fix function"""
    print("🔧 Fixing Missing Methods in Pairlist Generator")
    print("=" * 60)
    
    if fix_pairlist_generator():
        if test_fix():
            print("\n✅ Fix successful!")
            print("🚀 Now try: python3 pairlist_generator.py --quote BTC --all")
        else:
            print("\n❌ Fix failed verification")
    else:
        print("\n❌ Fix failed")

if __name__ == "__main__":
    main()