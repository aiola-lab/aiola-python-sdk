from setuptools import setup, find_packages

setup(
    name="aiola-python-sdk",
    version="0.1.0",
    packages=find_packages(exclude=["tests*", "examples*"]),
    install_requires=[
        "python-socketio>=5.8.0",
        "websocket-client>=1.6.0",
        "sounddevice>=0.4.6",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "requests>=2.31.0",
        "numpy>=1.24.0",
        "aiohttp>=3.8.0",
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'black>=23.0.0',
            'isort>=5.0.0',
            'flake8>=6.0.0',
        ]
    },
    author="aiola",
    description="Python SDK for Aiola Streaming Service",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/aiola-streaming-sdk",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
) 