from setuptools import setup, find_packages

setup(
    name="laap-brain",
    version="3.1.0",
    description="LAAP Brain — 一行代码让任何智能体获得元认知/议会/知行合一。兼容Hermes/Claude Code/OpenClaw",
    long_description=open("SKILL.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="LAAP Team",
    author_email="team@laap.dev",
    url="https://github.com/laap/laap-brain",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=[],
    extras_require={
        "hermes": [],  # Hermes 检测自动启用
        "dev": ["pytest", "twine"],
    },
    entry_points={
        "console_scripts": [
            "laap-brain=laap_brain.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="agi, cognitive-architecture, meta-cognition, agent-framework, hermes, claude-code, openclaw",
)
