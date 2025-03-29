from setuptools import setup, find_packages

setup(
    name="boring_ai_gmaps_analytics",
    version="0.1.0",
    author="Jiryan Farokhi",
    description="A complete package for Analytics Data Gmaps with AI",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "pandas>=2.2.1",
        "openai",
        "flask"
    ],
    python_requires=">=3.9",
)