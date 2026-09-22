from setuptools import setup, find_packages

setup(
    name="time-protocol-sdk",
    version="2.0.0",
    author="COFC Technologies LTD",
    description="Official Python SDK & Interoperability Suite for TIME Protocol Core",
    py_modules=["time_sdk", "cash_adapter", "time_crypto", "time_ledger"],
    install_requires=["requests>=2.28.0"],
    python_requires=">=3.10",
)
