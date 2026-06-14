from setuptools import setup, find_packages

setup(
    name="laap-brain",
    version="5.0.0",
    description="LAAP Brain — Cognitive Enhancement Engine for AI Agents",
    long_description=open("README.md", encoding="utf-8").read() if __import__("os").path.exists("README.md") else "LAAP Brain v3.1",
    long_description_content_type="text/markdown",
    author="LAAP Team",
    url="https://github.com/lorryjovens-hub/laap-AGI-",
    py_modules=["laap_brain"],
    packages=["laap_brain"],
    package_dir={"laap_brain": "."},
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    entry_points={
        "console_scripts": [
            "laap-brain=laap_brain.__main__:main",
        ],
    },
)
