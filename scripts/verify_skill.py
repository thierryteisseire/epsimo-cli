
import subprocess
import sys
import json
import time
import os
import shutil

def run_command(cmd, capture_output=True):
    print(f"Running: {cmd}")
    # Add PYTHONPATH to find epsimo package
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True, env=env)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        raise Exception(f"Command failed: {cmd}")
    return result.stdout.strip()

def main():
    print("🚀 Starting Epsimo Agent Skill Verification (CLI Version)...")
    
    # 1. Auth Check - we do this in the root to ensure we have credentials
    print("\n1️⃣  Checking Authentication...")
    try:
        run_command("python3 -m epsimo.cli whoami") 
    except:
        print("🔐 Authentication required. Please run 'epsimo auth login' first.")
        sys.exit(1)
        
    # Setup temp workspace
    temp_workspace = f"verify-workspace-{int(time.time())}"
    os.makedirs(temp_workspace)
    orig_dir = os.getcwd()
    os.chdir(temp_workspace)
    print(f"📂 Created temporary workspace: {temp_workspace}")

    try:
        # 2. Project Scaffolding
        print("\n2️⃣  Verifying Project Scaffolding...")
        test_slug = "verify-app"
        run_command(f"python3 -m epsimo.cli create 'Verify App'")
        if os.path.exists(test_slug) and os.path.exists(f"{test_slug}/epsimo.yaml"):
            print("✅ Scaffolding SUCCESS: App structure created.")
        else:
            raise Exception("App structure missing files.")
        
        # 3. End-to-End lifecycle
        print("\n3️⃣  Verifying Project/Assistant Lifecycle...")
        proj_name = f"VerifyProj-{int(time.time())}"
        run_command(f"python3 -m epsimo.cli init --name '{proj_name}'")
        
        with open("epsimo.yaml", "r") as f:
            import yaml
            cfg = yaml.safe_load(f)
            project_id = cfg['project_id']
        
        print(f"✅ Created Project: {project_id}")
        
        # Deploy (creates assistant)
        run_command("python3 -m epsimo.cli deploy")
        print("✅ Deployed Assistant.")

        # Discovery Check
        asst_json = run_command(f"python3 -m epsimo.cli assistants --project-id {project_id} --json")
        assistants = json.loads(asst_json)
        if not assistants:
            raise Exception("No assistants found after deploy.")
        
        print(f"✅ Discovery SUCCESS: Found {len(assistants)} assistants.")

        # 4. Logic responsive check
        print("\n4️⃣  Checking Credits...")
        run_command("python3 -m epsimo.cli credits balance")
        print("✅ Logic Check: Responsive.")

    finally:
        os.chdir(orig_dir)
        if os.path.exists(temp_workspace):
            shutil.rmtree(temp_workspace)

    print("\n🎉 Skill Verification Completed Successfully!")

if __name__ == "__main__":
    main()

