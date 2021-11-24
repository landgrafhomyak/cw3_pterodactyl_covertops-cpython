from setuptools import setup

setup(
    name="cw3_kamikadze_bot",
    py_modules=["cw3_kamikadze_bot"],
    description="Bot for managing covert operations in Chat Wars",
    version="1.0rc2",
    author="Andrew Golovashevich",
    url="https://LandgrafHomyak.github.io/cw3_pterpdactyl_covertops-cpython/",
    download_url="https://github.com/LandgrafHomyak/cw3_pterpdactyl_covertops-cpython/releases/tag/1.0rc2",
    python_requires=">=3.8, <3.12",
    install_requires=[
        "aiogram",
        "sqlalchemy",
        "asyncpg",
        "chatwars-api @ git+https://github.com/LandgrafHomyak/cwapi-python.git@v1!2021.11.24b0"
    ],
    entry_points={
        "console_scripts": [
            "cw3_kamikadze_bot=cw3_kamikadze_bot:main"
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Plugins",
        "Framework :: AsyncIO",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: Russian",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Topic :: Games/Entertainment",
        "Topic :: Games/Entertainment :: Role-Playing",
        # "Typing :: Typed"
    ],
    license="MIT",
    license_files=["LICENSE"],
)
