from setuptools import setup

setup(
    name="cw3_kamikadze_bot",
    py_modules=["cw3_kamikadze_bot"],
    version="0.0rc0",
    python_requires=">=3.8",
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
)
