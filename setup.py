from setuptools import setup, find_packages

setup(
    name="Backtesting Engine",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)

# Run "pip install -e ." in terminal to install / update 
