import argparse
import re
import requests
import os
import subprocess
from hcl2 import loads

# Global variable to store the retrieved changelog paragraph
changelog_paragraph = ""


def is_valid_changelog(content, file_path):
    if not file_path.endswith('.txt'):
        return False, "The document is not in .txt format."
        exit()
    if not content.startswith('## '):
        return False, "The document is not a changelog from AWS."
        exit()

    # Use regex pattern to match version format (e.g., ## 4.0.0 (February 10, 2022) or ## 5.0.0 (Unreleased))
    first_line = content.split('\n')[0]
    pattern = r'##\s*\d+\.\d+\.\d+\s*\(.*\)'
    if not re.search(pattern, first_line):
        return False, "The first line of the document does not contain a valid date and version number format."

    keywords = ['resource', 'data-source', 'aws']
    for keyword in keywords:
        if keyword not in content.lower():
            return False, f"The document is missing the '{keyword}' keyword."

    return True, ""


def retrieve_first_paragraph_between_tags(content):
    global changelog_paragraph
    start_index = content.find('##')
    end_index = content.find('##', start_index + 2)

    if start_index != -1 and end_index != -1:
        retrieved_paragraph = content[start_index + 2:end_index].strip()
        changelog_paragraph = retrieved_paragraph
    else:
        changelog_paragraph = "First paragraph between tags not found."


def retrieve_changelog_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            changelog_content = file.read()
            return changelog_content
    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
        exit()


# def fetch_and_analyze_changelog(file_path):
#     # Retrieve changelog content from the file
#     changelog_content = retrieve_changelog_from_file(file_path)
#     if changelog_content is not None:
#         # Validate the changelog content and its format
#         is_valid, error_message = is_valid_changelog(changelog_content, file_path)
#         if is_valid:
#             # Extract the first paragraph between tags from the changelog
#             retrieve_first_paragraph_between_tags(changelog_content)
#             print("The changelog is retrieved.")
#         else:
#             print(f"Error: {error_message}")

def fetch_and_analyze_changelog(file_path):
    # Retrieve changelog content from the file
    changelog_content = retrieve_changelog_from_file(file_path)
    if changelog_content is not None:
        # Validate the changelog content and its format
        is_valid, error_message = is_valid_changelog(changelog_content, file_path)
        if is_valid:
            # Extract the first paragraph between tags from the changelog
            retrieve_first_paragraph_between_tags(changelog_content)
            print("The changelog is retrieved.")
        else:
            print(f"Error: {error_message}")
            return False, error_message
    else:
        print(f"Error: Failed to retrieve changelog content from '{file_path}'.")
        return False, "Failed to retrieve changelog content."
    return True, ""

# Rest of the code remains the same


def check_internet_connection():
    try:
        response = requests.get("https://www.google.com", timeout=5)
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.RequestException:
        return False


def validate_version_format(version):
    # Use regex pattern to match version format (e.g., vX.X.X)
    pattern = r'^v\d+\.\d+\.\d+$'
    if re.match(pattern, version):
        return True
    else:
        print(f"Invalid version format. Please use the pattern vX.X.X (e.g., v1.2.3).")
        exit()


def retrieve_changelog(version):
    global changelog_paragraph
    # Construct the URL for the changelog based on the given version
    changelog_url = f"https://raw.githubusercontent.com/hashicorp/terraform-provider-aws/{version}/CHANGELOG.md"
    response = requests.get(changelog_url)

    if response.status_code == 200:
        changelog_text = response.text
        start_tag = f"## {version}"
        start_index = changelog_text.find(start_tag) + len(version) + 4
        end_index = changelog_text.find('##', start_index)

        if start_index != -1 and end_index != -1:
            # Extract the changelog section for the specified version
            changelog_section = changelog_text[start_index:end_index].strip()
            changelog_paragraph = changelog_section
            print("The changelog is retrieved.")
        else:
            print(f"Changelog section for version {version} not found.")
            exit()
    else:
        print(f"Failed to retrieve the changelog for version {version}. Check if the version is valid.")
        exit()

def validate_changelog_content(changelog_text):
    if not changelog_text.startswith('##'):
        return False, "The document is not a valid changelog."

    # Use regex pattern to match version format (e.g., ## 4.0.0 (February 10, 2022))
    first_line = changelog_text.split('\n')[0]
    pattern = r'##\s*\d+\.\d+\.\d+\s*\(.*\)'
    if not re.search(pattern, first_line):
        return False, "The first line of the document does not contain a valid date and version number format."

    keywords = ['resource', 'data-source', 'aws']
    for keyword in keywords:
        if keyword not in changelog_text.lower():
            return False, f"The document is missing the '{keyword}' keyword."

    return True, ""


def validate_directory_path(path):
    if not os.path.exists(path):
        print(f"Error: The directory '{path}' does not exist.")
        return False
    if not os.path.isdir(path):
        print(f"Error: '{path}' is not a valid directory.")
        return False
    return True


# def list_terraform_files(directory_path):
#     tf_files = []
#     for root, dirs, files in os.walk(directory_path):
#         for file in files:
#             if file.endswith(".tf"):
#                 tf_files.append(os.path.join(root, file))
#     return tf_files



def list_terraform_files(directory_path):
    tf_files = []
    with os.scandir(directory_path) as entries:
        for entry in entries:
            if entry.is_file() and entry.name.endswith(".tf"):
                tf_files.append(entry.path)
            elif entry.is_dir():
                tf_files.extend(list_terraform_files(entry.path))
    return tf_files



def validate_terraform_file(file_path):
    try:
        # Run `terraform init` to initialize the project
        init_cmd = ['terraform', 'init']
        subprocess.run(init_cmd, capture_output=True, text=True, check=True, cwd=os.path.dirname(file_path))

        # Run `terraform validate` to validate the Terraform configuration
        validate_cmd = ['terraform', 'validate']
        result = subprocess.run(validate_cmd, capture_output=True, text=True, cwd=os.path.dirname(file_path), encoding='utf-8')

        # Display the command output, including error messages
        print(result.stdout)

        # Check if the validation command was successful
        if result.returncode == 0:
            return True
        else:
            print("Terraform validation error:")
            print(result.stderr)
            return False

    except subprocess.CalledProcessError as e:
        # Display the error message and return False
        print("Error validating Terraform file:")
        print(e.stderr)
        return False

# Find updates in Terraform files based on changelog
def find_updates(changelog, terraform_content):
    updates = []
    for line in changelog.split('\n'):
        # Use regex pattern to match changelog update format
        # match = re.match(r'\* .*/([^:]+): .* \(\[#\d+\]\(.*\)\)', line)  ## example: * data-source/aws_api_gateway_rest_api: `minimum_compression_size` is now a string type to allow values set via the `body` attribute to be properly computed. ([#30969](https://github.com/hashicorp/terraform-provider-aws/issues/30969))
        match = re.match(r'\* .*/([^:]+): .* \(\[#\d+\]\(.*\)\)', line)

        if match:
            data_source = match.group(1)
            update = match.group(0)
            if data_source in terraform_content:
                # Extract the corresponding Terraform block for the update
                block = extract_block(data_source, terraform_content)
                updates.append((update, block))
    return updates





# Extract a specific block from Terraform content
def extract_block(data_source, terraform_content):
    try:
        # Load Terraform content as an HCL2 tree
        hcl_tree = loads(terraform_content)
        
        # Get the list of "resource" blocks from the Terraform content
        resource_blocks = hcl_tree.get('resource', [])
        
        # Iterate through each resource block in the list
        for block in resource_blocks:
            # Get the resource type (e.g., "aws_instance")
            resource_type = list(block.keys())[0]  # Convert dict_keys to list
            
            # If the resource type matches the specified resource (data_source)
            if resource_type == data_source:
                # Return the content of the corresponding Terraform block for the resource
                return block[resource_type]
    except Exception as e:
        print("Error extracting block:", e)
    return None



# Analyze Terraform files in a directory
def analyze_terraform_files(directory_path, output_file, output_format, no_output):
    # Validate the provided directory path
    if validate_directory_path(directory_path):
        print(f"Terraform files in '{directory_path}':")
        # List all Terraform files in the specified directory
        tf_files = list_terraform_files(directory_path)
        if tf_files:
            # Iterate through each Terraform file
            for file_path in tf_files[:]:
                print(f"Analyzing file: {file_path}")
                # Validate the Terraform file
                is_valid = validate_terraform_file(file_path)
                if not is_valid:
                    user_choice = input("The Terraform file is invalid. Do you want to continue without this file? (yes/no): ")
                    if user_choice.lower() != "yes":
                        print("Exiting program.")
                        return
                    else:
                        tf_files.remove(file_path)

            print("\nList of valid Terraform files:")
            for file_path in tf_files:
                print(file_path)

            # Process output data if output is not suppressed
            if not no_output:
                output_data = ""
                for file_path in tf_files:
                    # Read the Terraform content from the file
                    with open(file_path, 'r') as f:
                        terraform_content = f.read()

                    # Find updates in the Terraform file based on the retrieved changelog paragraph
                    updates = find_updates(changelog_paragraph, terraform_content)

                    if updates:
                        output_data += "/" * 40 + "\n"
                        output_data += f"Updates to be made in Terraform file '{file_path}':\n"
                        # Iterate through each update and corresponding block
                        for update, block in updates:
                            output_data += f"Update : {update}\n"
                            if block:
                                output_data += "Corresponding Terraform block:\n"
                                output_data += format_as_terraform(block) + "\n"



                            output_data += "=" * 40 + "\n"
                      
                    else:
                        output_data += f"No updates needed for Terraform file '{file_path}'.\n"
                        output_data += "=" * 40 + "\n"
                # Write output data to the specified output file or display in the command line
                if output_file:
                    if output_format:
                        output_file = f"{output_file}.{output_format}"
                    with open(output_file, 'w') as f:
                        f.write(output_data)
                    print(f"Output written to '{output_file}'.")
                else:
                    print(output_data)
        else:
            print(f"No Terraform files found in '{directory_path}'.")


def format_as_terraform(data, level=0):
    indent = "  " * level  # Create an indentation to make the code readable
    formatted = ""  # Initialize an empty string to store the formatted code

    # Iterate through each key-value pair in the 'data' dictionary
    for key, value in data.items():
        if isinstance(value, dict):
            # If the value is another dictionary, it signifies a nested Terraform block
            formatted += f"{indent}{key} {{\n"  # Start the Terraform block with an opening brace
            formatted += format_as_terraform(value, level + 1)  # Recursively call the function to format the nested block
            formatted += f"{indent}}}\n"  # End the Terraform block with a closing brace
        else:
            formatted += f'{indent}{key} = '  # Add the key to the Terraform line
            if isinstance(value, str):
                formatted += f'"{value}"\n'  # If the value is a string, enclose it in double quotes
            else:
                formatted += f"{value}\n"  # Otherwise, leave the value as it is

    return formatted  # Return the formatted Terraform code



# Main function to handle command-line arguments and execution
# def main():
#     parser = argparse.ArgumentParser(description="Retrieve an AWS changelog or analyze Terraform files.")
#     parser.add_argument('-c', '--changelog', type=str, help="Path to the changelog file.")
#     parser.add_argument("-r", "--remote", type=str, help="Retrieve the changelog for the specified version.")
#     parser.add_argument("-p", "--path", type=str, help="Path to the directory to analyze Terraform files.")
#     parser.add_argument("-o", "--output", type=str, help="Path to the output file for saving the analysis.")
#     parser.add_argument("-f", "--output-format", type=str, help="Output file format (e.g., txt, md).")
#     parser.add_argument("--no-output", action="store_true", help="Display output in command line and do not save to a file.")

#     args = parser.parse_args()



#     if args.changelog and args.path:
#         if check_internet_connection():
#             fetch_and_analyze_changelog(args.changelog)
#         else:
#             print("Your machine is not connected to the Internet.")
#         analyze_terraform_files(args.path, args.output, args.output_format, args.no_output)
#     elif args.remote and args.path:
#         version = args.remote
#         if check_internet_connection():
#             validate_version_format(version)
#             retrieve_changelog(version)
#         analyze_terraform_files(args.path, args.output, args.output_format, args.no_output)
#     else:
#         print("Please provide either -c with a path and -p with a path, or -r with a version and -p with a path.")

# if __name__ == "__main__":
#     main()



def main():
    parser = argparse.ArgumentParser(description="Retrieve an AWS changelog or analyze Terraform files.")
    parser.add_argument('-c', '--changelog', type=str, help="Path to the changelog file.")
    parser.add_argument("-r", "--remote", type=str, help="Retrieve the changelog for the specified version.")
    parser.add_argument("-p", "--path", type=str, help="Path to the directory to analyze Terraform files.")
    parser.add_argument("-o", "--output", type=str, help="Path to the output file for saving the analysis.")
    parser.add_argument("-f", "--output-format", type=str, help="Output file format (e.g., txt, md).")
    parser.add_argument("--no-output", action="store_true", help="Display output in command line and do not save to a file.")

    args = parser.parse_args()

    if args.changelog and args.path:
        if check_internet_connection():
            is_valid, error_message = fetch_and_analyze_changelog(args.changelog)
            if not is_valid:
                print(f"Error: {error_message}")
                return
        else:
            print("Your machine is not connected to the Internet.")
            return
        analyze_terraform_files(args.path, args.output, args.output_format, args.no_output)

    elif args.remote and args.path:
        version = args.remote
        if check_internet_connection():
            if validate_version_format(version):
                retrieve_changelog(version)
            analyze_terraform_files(args.path, args.output, args.output_format, args.no_output)
        else:
            exit()

    elif args.remote and args.changelog:
        print("Please provide either -c with a path and -p with a path, or -r with a version and -p with a path.")

    elif args.remote and args.changelog and args.path:
        print("Please provide either -c with a path and -p with a path, or -r with a version and -p with a path.")

    else:
        print("Please provide either -c with a path and -p with a path, or -r with a version and -p with a path.")

  

if __name__ == "__main__":
    main()

