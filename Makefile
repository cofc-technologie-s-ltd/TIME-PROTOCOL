.PHONY: test sdk-ts sdk-go sdk-rust clean

test:
python -m unittest test_pure_core.py

sdk-ts:
@echo "TypeScript SDK is located in sdks/typescript"

sdk-go:
@echo "Go SDK is located in sdks/go"

sdk-rust:
cd sdks/rust && cargo check

clean:
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
@echo "Cleaned temporary Python cache files."
