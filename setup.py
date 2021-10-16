from setuptools import setup

setup(
    name="cw3_kamikadze_bot",
    py_modules =["cw3_kamikadze_bot"],
    version="0.0rc0",
    python_requires=">=3.8",
    install_requires=["aiogram", "sqlalchemy", "asyncpg"],
    entry_points={
        "console_scripts": [
            "cw3_kamikadze_bot=cw3_kamikadze_bot:main"
        ]
    },
)