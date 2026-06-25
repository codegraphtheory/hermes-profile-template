import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add scripts directory to path to allow importing scorecard and validation scripts
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import profile_wizard
import validate_profile


class TestProfileWizard(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for outputs
        self.test_dir = tempfile.TemporaryDirectory()
        self.output_path = Path(self.test_dir.name) / "test-wizard-profile"
        
    def tearDown(self):
        # Clean up temporary directory
        self.test_dir.cleanup()

    def test_non_interactive_generation(self):
        """Test wizard in non-interactive mode generates a valid profile."""
        with patch("sys.argv", [
            "profile_wizard.py",
            "--non-interactive",
            "--name", "non-interactive-profile",
            "--description", "This is a non-interactive test description.",
            "--output", str(self.output_path)
        ]):
            try:
                code = profile_wizard.main()
            except SystemExit as exc:
                code = exc.code
                
            self.assertEqual(code, 0)
            self.assertTrue((self.output_path / "distribution.yaml").is_file())
            self.assertTrue((self.output_path / "profile.params.yaml").is_file())
            
            # Run validator on the output
            errors = []
            validate_profile.check_required(self.output_path, errors)
            validate_profile.check_manifest(self.output_path, errors)
            validate_profile.check_json(self.output_path, errors)
            validate_profile.check_skills(self.output_path, errors)
            validate_profile.check_forbidden_paths(self.output_path, errors)
            validate_profile.check_symlinks(self.output_path, errors)
            validate_profile.check_secrets(self.output_path, errors)
            
            self.assertEqual(len(errors), 0, f"Validation errors: {errors}")

    def test_interactive_mock_inputs_full(self):
        """Test interactive mode with custom mock inputs."""
        inputs = [
            "custom-interactive-profile",  # Name
            "Custom Interactive Profile",  # Display Name
            "This is a custom interactive test description.",  # Description
            "Developers, Admins",  # Target Users
            "file, terminal",  # Toolsets
            "TEST_API_KEY, OTHER_KEY",  # Required env vars
            "y",  # Is TEST_API_KEY required
            "Test API Key for validation",  # TEST_API_KEY description
            "n",  # Is OTHER_KEY required
            "Other optional key description",  # OTHER_KEY description
            "y",  # Include profile-craft skill
            "Do not allow file deletion",  # Refusal 1
            "Do not perform destructive operations",  # Refusal 2
            "",  # Done with refusals
            str(self.output_path)  # Output directory
        ]
        
        with patch("builtins.input", side_effect=inputs), patch("sys.argv", ["profile_wizard.py"]):
            try:
                code = profile_wizard.main()
            except SystemExit as exc:
                code = exc.code
                
            self.assertEqual(code, 0)
            self.assertTrue((self.output_path / "profile.params.yaml").is_file())
            
            # Verify custom properties were saved to profile.params.yaml
            import yaml
            params = yaml.safe_load((self.output_path / "profile.params.yaml").read_text(encoding="utf-8"))
            self.assertEqual(params["name"], "custom-interactive-profile")
            self.assertEqual(params["display_name"], "Custom Interactive Profile")
            self.assertEqual(params["description"], "This is a custom interactive test description.")
            self.assertEqual(params["toolsets"], ["file", "terminal"])
            
            env_vars = params["env_requires"]
            self.assertEqual(len(env_vars), 2)
            self.assertEqual(env_vars[0]["name"], "TEST_API_KEY")
            self.assertEqual(env_vars[0]["required"], True)
            self.assertEqual(env_vars[1]["name"], "OTHER_KEY")
            self.assertEqual(env_vars[1]["required"], False)
            
            self.assertIn("Do not allow file deletion", params["refusals"])
            self.assertIn("Do not perform destructive operations", params["refusals"])

    def test_interactive_mock_inputs_defaults(self):
        """Test interactive mode fallback defaults when inputs are empty."""
        inputs = [
            "interactive-default-profile",  # Name
            "",  # Display Name (fallback to Interactive Default Profile)
            "A profile with default settings.",  # Description
            "",  # Target Users (fallback to Developers)
            "",  # Toolsets (fallback to all defaults)
            "",  # Required env vars (fallback to none)
            "y",  # Include profile-craft
            "",  # Safety boundaries (fallback to default list)
            str(self.output_path)  # Output directory
        ]
        
        with patch("builtins.input", side_effect=inputs), patch("sys.argv", ["profile_wizard.py"]):
            try:
                code = profile_wizard.main()
            except SystemExit as exc:
                code = exc.code
                
            self.assertEqual(code, 0)
            self.assertTrue((self.output_path / "profile.params.yaml").is_file())
            
            import yaml
            params = yaml.safe_load((self.output_path / "profile.params.yaml").read_text(encoding="utf-8"))
            self.assertEqual(params["display_name"], "Interactive Default Profile")
            self.assertEqual(params["toolsets"], ["file", "terminal", "skills", "web", "session_search", "clarify"])
            self.assertEqual(params["env_requires"], [])

    def test_skip_skills(self):
        """Test that opting out of bundling skills deletes the skill folder."""
        inputs = [
            "skip-skills-profile",  # Name
            "",  # Display Name
            "Description.",  # Description
            "",  # Target Users
            "",  # Toolsets
            "",  # Required env vars
            "n",  # Include profile-craft (NO)
            "",  # Safety boundaries
            str(self.output_path)  # Output directory
        ]
        
        with patch("builtins.input", side_effect=inputs), patch("sys.argv", ["profile_wizard.py"]):
            try:
                code = profile_wizard.main()
            except SystemExit as exc:
                code = exc.code
                
            self.assertEqual(code, 0)
            
            # Verify the skill folder was cleaned up/deleted
            self.assertFalse((self.output_path / "skills" / "profile-craft").exists())

    def test_missing_required_args_non_interactive(self):
        """Test that missing required parameters in non-interactive mode raises SystemExit with code 1."""
        with patch("sys.argv", ["profile_wizard.py", "--non-interactive", "--name", "incomplete-profile"]):
            try:
                code = profile_wizard.main()
            except SystemExit as exc:
                code = exc.code
            
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
