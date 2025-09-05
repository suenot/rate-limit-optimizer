"""
Setup script for Rate Limit Optimizer
"""
from setuptools import setup, find_packages
from pathlib import Path

# Читаем README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Читаем requirements
requirements = []
requirements_path = this_directory / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Убираем комментарии из строки
                requirement = line.split('#')[0].strip()
                if requirement:
                    requirements.append(requirement)

setup(
    name="rate-limit-optimizer",
    version="1.0.0",
    author="Rate Limit Optimizer Team",
    author_email="team@ratelimitoptimizer.com",
    description="Автоматическое определение и оптимизация rate limits API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/rate-limit-optimizer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
        "Topic :: Utilities",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.0.0",
        ],
        "all": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "rate-limit-optimizer=rate_limit_optimizer.main:main",
            "rlo=rate_limit_optimizer.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "rate_limit_optimizer": [
            "*.json",
            "*.yaml",
            "*.yml",
        ],
    },
    keywords=[
        "rate-limit",
        "api",
        "optimization",
        "testing",
        "performance",
        "monitoring",
        "ai",
        "automation"
    ],
    project_urls={
        "Bug Reports": "https://github.com/your-org/rate-limit-optimizer/issues",
        "Source": "https://github.com/your-org/rate-limit-optimizer",
        "Documentation": "https://rate-limit-optimizer.readthedocs.io/",
    },
)
