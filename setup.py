"""Setup script for st-auth-simple package."""

from setuptools import setup, find_packages

setup(
    name="st-auth-simple",
    version="1.0.2",
    packages=find_packages(exclude=["tests", "docs", "_pm", "*.egg-info"]),
    include_package_data=True,
    install_requires=[
        "streamlit>=1.56.0",
        "pycryptodome>=3.23.0",
        "python-dotenv>=1.0.1",
        "sendgrid>=6.11.0",
    ],
    extras_require={
        "airtable": ["pyairtable>=3.3.0"],
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.960",
        ],
    },
    python_requires=">=3.8",
    author="Arvindra Sehmi",
    author_email="asehmi@cloudopti.io",
    description="Simple username/password authentication for Streamlit apps with server-side session tokens and pluggable storage backends (includes optional email signup)",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/asehmi/auth-simple-for-streamlit",
    project_urls={
        "Documentation": "https://github.com/asehmi/auth-simple-for-streamlit#readme",
        "Repository": "https://github.com/asehmi/auth-simple-for-streamlit.git",
        "Issues": "https://github.com/asehmi/auth-simple-for-streamlit/issues",
    },
    license="MIT",
    keywords="streamlit authentication auth login security",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    zip_safe=False,
)
