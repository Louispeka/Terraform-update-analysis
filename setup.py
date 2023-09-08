from setuptools import setup

setup(
    name="terraform_analysis",
    version="1.0",
    author="Van Elsuve Louis",
    author_email="louis.vanelsuver@foundever.com",
    description=("Tfanalysis is a command line tool to scan Terraform files, retrieve a specify changelog and return potentials updates"),
    url="https://gitlab.eks.tools.icx.foundever.com/devops/products/terraform-update-analysis",
    py_modules=['tfanalysis'],
    install_requires=["requests","python-hcl2"],
    python_requires=">=3.0",
    entry_points={
        "console_scripts": [
            "tfanalysis = tfanalysis:main",
        ]
    }
)
