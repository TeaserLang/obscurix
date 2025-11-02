# Obscurix

Obscurix is an esoteric programming language (Esolang) designed to have an obscure syntax that is still binary-readable.

This package provides an interpreter for `.obx` files.

## Installation
```bash
pip install obscurix
```

## Using the CLI

Run Obscurix files from the command line:
```bash
python -m obscurix sample.obx
```

With `--debug` flag:
```bash
python -m obscurix --debug sample.obx
```

## Example code (`sample.obx`)
```obx
⥀ §sum_safe α β ※ Function definition: §sum_safe
  ⍟ ≔ 0 
  
  ↜ ?
α ≺ 0 ※ IF: Check condition α < 0
    ⇒ λ!
"Tham_số_âm" ※ TRUE: Throw an error
  ⇏ ※ ELSE: Otherwise
    ⍟ ≔ α ⊞ β ※ Calculate sum: ⍟ = α + β
  ↯ ※ End of IF block
  
  ⎋ ⍟ ※ Return the result variable ⍟
⥁ ※ End of function definition

* "Bắt_đầu_Chương_Trình" ※ Print start message

⛌ ※ TRY: Start protected block
  ⍡ ≔ 5 
  
  ⍟_res ≔ §sum_safe ⍡ 10 ※ Call function (5 + 10)
  * ⍟_res ※ Print result 15
  
  §sum_safe -1 10 ※ Call function with negative parameter -> THROW error
⎁ ε ※ CATCH: Catch error and store it in variable ε
  * "Lỗi_Bị_Bắt:" ※ Print catch message
  * ε ※ Print error message
⎎ ※ FINALLY: Block that always executes
  * "Kết_thúc_Xử_Lý_Lỗi" ※ Print finally message
⍰ ※ End of TRY block

* "Kết_thúc_Chương_Trình" ※ Print end message
```

## Using in code (Import)
```python
from obscurix.interpreter import ObscurixRuntime

# Source file path
FILENAME = "sample.obx"

# Initialize runtime and pass the required filename
runtime = ObscurixRuntime(FILENAME, debug=False) # Set this as True to enable debug log

# Run the execution (file content is read during initialization)
runtime.run()

# --- Expected Output (Vietnamese strings are part of the sample Obscurix code) ---
# Bắt_đầu_Chương_Trình
# 15
# Lỗi_Bị_Bắt:
# Tham_số_âm
# Kết_thúc_Xử_Lý_Lỗi
# Kết_thúc_Chương_Trình
```

## License

[MIT](LICENSE)
