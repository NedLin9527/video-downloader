"""套件探索與依賴設定；專案中繼資料位於 pyproject.toml。"""

from setuptools import find_packages, setup

with open("requirements.txt", encoding="utf-8") as requirements_file:
    requirements = [line.strip() for line in requirements_file
                    if line.strip() and not line.startswith("#")]

setup(
    packages=find_packages(include=["src", "src.*"]),
    package_data={"src.web": ["templates/*.html", "static/*"]},
    install_requires=requirements,
)
