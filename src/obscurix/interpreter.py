# This file contains the core parser and runtime logic for the Obscurix language.
# (Logic for _execute_block has been completely refactored to be command-oriented)
# (Includes --debug flag and FIX for Tokenizer merge and Executor ASSIGN logic)

import re

# Obscurix Constants (Symbols)
FUNC_START = '⥀'
FUNC_END = '⥁'
IF_START = '↜'
IF_COND = '?'
IF_THEN = '⇒'
IF_ELSE = '⇏'
IF_END = '↯'
TRY_START = '⛌'
CATCH = '⎁'
FINALLY = '⎎'
TRY_END = '⍰'
ASSIGN = '≔'
ADD = '⊞'
SUB = '⊖'
CALL = '§' 
PRINT = '*'
THROW = 'λ!'
RETURN = '⎋'
LT = '≺' 
EQ = '≡' 
RESULT_VAR = '⍟'
TEMP_VAR = '⍡'

# --- List of all symbols that are standalone tokens ---
# (Used by tokenizer and executor)
STANDALONE_SYMBOLS = [
    FUNC_START, FUNC_END, IF_START, IF_COND, IF_THEN, IF_ELSE, IF_END, 
    TRY_START, CATCH, FINALLY, TRY_END, THROW, RETURN, ASSIGN, 
    ADD, SUB, LT, EQ
]

class ObscurixRuntime:
    """ Simple interpreter for the Obscurix language. """
    def __init__(self, filename, debug=False): # Added debug flag
        self.functions = {}
        # Global symbol table
        self.symbol_table = {}
        self.filename = filename
        self.debug = debug # Store debug state
        
        self._log_debug(f"Initializing runtime for '{filename}'...")
        
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                self.source_code = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: '{filename}'")

    def _log_debug(self, message):
        """ Helper function for debug logging. """
        if self.debug:
            print(f"[DEBUG] {message}")

    def _tokenize(self):
        """ Tokenizes the source code. """
        self._log_debug("Starting tokenizer...")
        lines = self.source_code.splitlines()
        code_without_comments = []
        for line in lines:
            # Remove comments first
            line_clean = re.sub(r'※.*', '', line).strip()
            if line_clean:
                code_without_comments.append(line_clean)

        # Join all lines into a single string for parsing
        code_string = ' '.join(code_without_comments)
        self._log_debug(f"Cleaned code string: {code_string[:50]}...")
        
        # Pad symbols with spaces to ensure they are tokenized correctly
        for symbol in STANDALONE_SYMBOLS:
            code_string = code_string.replace(symbol, f' {symbol} ')
        
        # Split by spaces and remove empty tokens
        tokens = [token.strip() for token in code_string.split() if token.strip()]
        
        # --- Tokenizer Post-Processing (FIX for §func and *var) ---
        self._log_debug("Starting tokenizer post-processing (merge)...")
        merged_tokens = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            # Check if token is CALL (§) or PRINT (*)
            if (token == CALL or token == PRINT) and (i + 1 < len(tokens)):
                next_token = tokens[i+1]
                # If the next token is NOT another symbol, merge them
                if next_token not in STANDALONE_SYMBOLS and next_token not in [CALL, PRINT]:
                    merged_tokens.append(f"{token}{next_token}")
                    self._log_debug(f"Merged token: {token}{next_token}")
                    i += 2 # Skip both tokens
                    continue
            
            merged_tokens.append(token)
            i += 1
        
        self._log_debug(f"Generated {len(merged_tokens)} tokens (after merge).")
        self._log_debug(f"Token sample: {merged_tokens[:10]}")
                
        return merged_tokens

    def _get_value(self, token, scope):
        """ 
        Retrieves the value of a token (literal or variable).
        """
        self._log_debug(f"Getting value for token: '{token}'")
        if token.startswith('"') and token.endswith('"'):
            return token.strip('"')

        try:
            return int(token)
        except ValueError:
            pass
        
        if token in scope:
            self._log_debug(f"Found '{token}' in local scope.")
            return scope[token]
        
        if token in self.symbol_table:
            self._log_debug(f"Found '{token}' in global scope.")
            return self.symbol_table[token]

        raise Exception(f"Undefined variable/symbol: {token}")

    def _evaluate_expression(self, expr_tokens, scope):
        """ Evaluates a simple expression (e.g., a + b or a function call). """
        self._log_debug(f"Evaluating expression: {expr_tokens}")
        
        if not expr_tokens:
            raise Exception("Invalid expression: Empty expression.")

        # Case 1: Function Call
        if expr_tokens[0].startswith(CALL):
            return self._execute_function_call(expr_tokens, scope)

        # Case 2: Simple Value
        if len(expr_tokens) == 1:
            return self._get_value(expr_tokens[0], scope)
        
        # Case 3: Binary Operation (a + b)
        if len(expr_tokens) == 3:
            op1 = self._get_value(expr_tokens[0], scope)
            operator = expr_tokens[1]
            op2 = self._get_value(expr_tokens[2], scope)

            if operator == ADD:
                return op1 + op2
            if operator == SUB:
                return op1 - op2
            if operator == LT:
                return op1 < op2
            if operator == EQ:
                return op1 == op2

        raise Exception(f"Invalid expression: {' '.join(expr_tokens)}")

    def _execute_function_call(self, tokens, scope):
        """ Executes a function call. Returns the function's result. """
        func_name = tokens[0] # This is now '§func_name'
        args = tokens[1:]
        self._log_debug(f"Executing function call: {func_name} with args: {args}")
        
        if func_name not in self.functions:
            raise Exception(f"Function not found: {func_name}")

        func_def = self.functions[func_name]
        params = func_def['params']
        func_body = func_def['body']

        if len(args) != len(params):
            raise Exception(f"Parameter error when calling {func_name}. Required {len(params)}, received {len(args)}.")

        # Create a new scope for the function
        func_scope = self.symbol_table.copy() # Start with global scope
        func_scope.update(scope) # Add parent scope (for nesting)
        
        for i, param_name in enumerate(params):
            arg_value = self._get_value(args[i], scope)
            self._log_debug(f"Setting param '{param_name}' = {arg_value}")
            func_scope[param_name] = arg_value
        
        try:
            self._execute_block(func_body, 0, func_scope)
        except StopIteration as return_value:
            # Handle RETURN (⎋)
            self._log_debug(f"Function {func_name} returned value: {return_value.value}")
            return return_value.value
        except Exception as e:
            raise e # Propagate other exceptions
            
        self._log_debug(f"Function {func_name} finished (void).")
        return None # No return value (void function)

    def _find_matching_end(self, tokens, start_index, start_token, end_token):
        """ Finds the matching end token for a block (e.g., ⛌ -> ⍰) """
        self._log_debug(f"Finding matching '{end_token}' for '{start_token}' starting at index {start_index}")
        nest_level = 0
        for i in range(start_index, len(tokens)):
            if tokens[i] == start_token:
                nest_level += 1
            elif tokens[i] == end_token:
                nest_level -= 1
                if nest_level == 0:
                    self._log_debug(f"Found matching end at index {i}")
                    return i
        raise Exception(f"Syntax error: Missing '{end_token}' for '{start_token}'.")
        
    def _is_command_starter(self, token):
        """ 
        Checks if a token is the start of a new, standalone command.
        *** THIS IS THE BUG FIX ***
        '§' (CALL) is NO LONGER considered a standalone starter, 
        as it can be part of an ASSIGN expression.
        """
        return token.startswith(PRINT) or \
               token in [IF_START, TRY_START, THROW, RETURN]
    
    def _is_block_end(self, token):
        """ Checks if a token is a block terminator. """
        return token in [FUNC_END, IF_END, TRY_END, IF_ELSE, CATCH, FINALLY]

    def _execute_block(self, tokens, start_index, scope):
        """ 
        REFACTORED: Executes a block of tokens, command by command.
        Returns the index of the next token to be processed (after the block ends).
        """
        self._log_debug(f"Executing block starting at index {start_index}")
        i = start_index
        while i < len(tokens):
            token = tokens[i]
            self._log_debug(f"Processing token [{i}]: '{token}'")

            # --- End of Block Markers (Stop execution) ---
            if self._is_block_end(token):
                self._log_debug(f"Hit block end marker '{token}'. Returning control.")
                return i # Return control to the calling block

            # --- Handle Print (PRINT) ---
            elif token.startswith(PRINT):
                var_name = token[1:] # Get the variable/string part
                if not var_name:
                    raise Exception(f"Syntax error: '{PRINT}' command must be followed by a value.")
                
                self._log_debug(f"Command: PRINT. Target: '{var_name}'")
                value_to_print = self._get_value(var_name, scope)
                print(value_to_print)
                i += 1 # Skip this token
                continue

            # --- Handle Throw (THROW) ---
            elif token == THROW:
                if i + 1 >= len(tokens):
                    raise Exception(f"Syntax error: '{THROW}' command must be followed by a message.")
                
                message = self._get_value(tokens[i+1], scope)
                self._log_debug(f"Command: THROW. Message: '{message}'")
                i += 2
                raise Exception(message) 

            # --- Handle Return (RETURN) ---
            elif token == RETURN:
                if i + 1 >= len(tokens):
                    raise Exception(f"Syntax error: '{RETURN}' command must be followed by a value.")
                
                value_to_return = self._get_value(tokens[i+1], scope)
                self._log_debug(f"Command: RETURN. Value: '{value_to_return}'")
                i += 2
                raise StopIteration(value_to_return) # Use StopIteration to signal return

            # --- Handle Standalone Function Call (CALL) ---
            elif token.startswith(CALL):
                self._log_debug(f"Command: Standalone CALL '{token}'")
                # Finds the end of the function call (before the next command)
                expr_start = i
                expr_end = i + 1
                while expr_end < len(tokens):
                    if self._is_command_starter(tokens[expr_end]) or \
                       self._is_block_end(tokens[expr_end]) or \
                       (expr_end + 1 < len(tokens) and tokens[expr_end + 1] == ASSIGN):
                        break
                    expr_end += 1
                
                call_tokens = tokens[expr_start:expr_end]
                self._execute_function_call(call_tokens, scope)
                i = expr_end
                continue

            # --- Handle Assignment (ASSIGN) ---
            # Check if token[i+1] is ASSIGN
            elif i + 1 < len(tokens) and tokens[i+1] == ASSIGN:
                target_var = tokens[i]
                self._log_debug(f"Command: ASSIGN. Target: '{target_var}'")
                
                # *** THIS IS THE BUG FIX (Find end of expression) ***
                expr_start = i + 2
                expr_end = expr_start
                while expr_end < len(tokens):
                    t = tokens[expr_end]
                    # Stop if the *current* token starts a new command
                    if self._is_command_starter(t):
                        break
                    # Stop if the *current* token is a block end
                    if self._is_block_end(t):
                        break
                    # Stop if the *next* token is an assignment
                    if expr_end + 1 < len(tokens) and tokens[expr_end+1] == ASSIGN:
                        break
                    expr_end += 1
                
                expr_tokens = tokens[expr_start:expr_end]
                # *** END OF BUG FIX ***
                
                if not expr_tokens:
                     raise Exception(f"Syntax error: Missing expression for assignment to '{target_var}'.")

                self._log_debug(f"Assigning expression: {expr_tokens}")
                result = self._evaluate_expression(expr_tokens, scope)
                
                if target_var.startswith(CALL) or target_var.startswith(PRINT):
                     raise Exception(f"Cannot assign to command: {target_var}")

                # Assign to the correct scope
                if target_var in scope:
                    scope[target_var] = result
                else:
                    self.symbol_table[target_var] = result
                    
                self._log_debug(f"Assigned {target_var} = {result}")
                i = expr_end # Continue from after the expression
                continue
            
            # --- Handle IF Block ---
            elif token == IF_START:
                self._log_debug(f"Command: IF_START '{token}'")
                if_end_index = self._find_matching_end(tokens, i, IF_START, IF_END)
                
                cond_index = -1
                try: cond_index = tokens.index(IF_COND, i, if_end_index)
                except ValueError: raise Exception(f"Syntax error: Missing '{IF_COND}' for '{IF_START}'.")

                # *** BUG FIX START ***
                # Tìm '⇒' (THEN) *trước* khi đánh giá
                then_index = -1
                try: then_index = tokens.index(IF_THEN, cond_index, if_end_index)
                except ValueError: raise Exception(f"Syntax error: Missing '{IF_THEN}' for '{IF_START}'.")
                
                # Biểu thức điều kiện nằm giữa '?' (cond_index) và '⇒' (then_index)
                cond_expr = tokens[cond_index + 1 : then_index]
                
                if not cond_expr:
                    raise Exception("Invalid expression: Empty IF condition.")
                # *** BUG FIX END ***

                condition_result = self._evaluate_expression(cond_expr, scope)
                self._log_debug(f"IF condition result: {condition_result}")
                
                else_index = -1
                try: 
                    else_index_check = tokens.index(IF_ELSE, then_index, if_end_index)
                    else_index = else_index_check
                except ValueError: pass # No ELSE block is fine

                if condition_result:
                    self._log_debug("Executing THEN block.")
                    self._execute_block(tokens, then_index + 1, scope)
                elif else_index != -1:
                    self._log_debug("Executing ELSE block.")
                    self._execute_block(tokens, else_index + 1, scope)
                else:
                    self._log_debug("Condition false, no ELSE block.")
                
                i = if_end_index + 1
                continue

            # --- Handle TRY/CATCH Block ---
            elif token == TRY_START:
                self._log_debug(f"Command: TRY_START '{token}'")
                try_end_index = self._find_matching_end(tokens, i, TRY_START, TRY_END)
                catch_index = -1
                finally_index = -1

                try: 
                    catch_index_check = tokens.index(CATCH, i, try_end_index)
                    catch_index = catch_index_check
                except ValueError: pass # No CATCH block
                
                try: 
                    finally_index_check = tokens.index(FINALLY, i, try_end_index)
                    finally_index = finally_index_check
                except ValueError: pass # No FINALLY block

                try_block_start = i + 1
                catch_error_var = tokens[catch_index + 1] if catch_index != -1 else None
                catch_block_start = catch_index + 2 if (catch_index != -1 and catch_index + 1 < try_end_index) else -1
                finally_block_start = finally_index + 1 if finally_index != -1 else -1
                
                try:
                    self._log_debug("Executing TRY block.")
                    self._execute_block(tokens, try_block_start, scope)
                except Exception as e:
                    self._log_debug(f"TRY block raised exception: {e}")
                    if catch_block_start != -1:
                        self._log_debug(f"Executing CATCH block. Assigning error to '{catch_error_var}'")
                        scope[catch_error_var] = str(e) # Assign error message to 'ε'
                        self._execute_block(tokens, catch_block_start, scope)
                    else:
                        self._log_debug("No CATCH block. Re-throwing exception.")
                        raise e # Re-throw if no CATCH
                finally:
                    if finally_block_start != -1:
                        self._log_debug("Executing FINALLY block.")
                        self._execute_block(tokens, finally_block_start, scope)
                
                i = try_end_index + 1
                continue

            else:
                # This token is not a command.
                raise Exception(f"Syntax error: Unexpected token '{token}'")
        
        self._log_debug("Reached end of block.")
        return i # End of tokens

    def run(self):
        """ Parses and executes the source code. """
        tokens = []
        try:
            tokens = self._tokenize()
        except Exception as e:
            print(f"!!! TOKENIZER ERROR !!!\n{e}")
            return

        if not tokens:
            return

        # --- STEP 1: DEFINE FUNCTIONS ---
        self._log_debug("Starting Pass 1: Function Definition")
        global_tokens = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if token == FUNC_START:
                func_end_index = -1
                try:
                    func_end_index = self._find_matching_end(tokens, i, FUNC_START, FUNC_END)
                except Exception as e:
                    print(f"!!! PARSE ERROR (Function Definition) !!!\n{e}")
                    return

                func_def_tokens = tokens[i+1:func_end_index]
                
                if not func_def_tokens or not func_def_tokens[0].startswith(CALL):
                    raise Exception("Missing function name or § symbol in definition.")
                
                func_name = func_def_tokens[0] # This is now '§func_name'
                
                # Find where parameters end and body begins
                body_start_index = 1
                while body_start_index < len(func_def_tokens):
                    t = func_def_tokens[body_start_index]
                    if self._is_command_starter(t) or \
                       self._is_block_end(t) or \
                       (body_start_index + 1 < len(func_def_tokens) and func_def_tokens[body_start_index+1] == ASSIGN):
                        break
                    body_start_index += 1
                
                params = func_def_tokens[1:body_start_index]
                func_body = func_def_tokens[body_start_index:]
                
                self.functions[func_name] = {
                    'params': params,
                    'body': func_body
                }
                self._log_debug(f"Defined function: {func_name} with params {params}")
                
                i = func_end_index + 1 
            else:
                global_tokens.append(token)
                i += 1

        # --- STEP 2: EXECUTE GLOBAL SCOPE ---
        self._log_debug(f"Starting Pass 2: Global Execution ({len(global_tokens)} tokens)")
        try:
            # Execute global scope with the global symbol table
            self._execute_block(global_tokens, 0, self.symbol_table)
        except StopIteration:
            print("!!! FATAL ERROR: 'RETURN' (⎋) command found in global scope.")
        except Exception as e:
            # FIX: Removed the invalid escape sequence \S
            print(f"!!! UNHANDLED PROGRAM ERROR !!!\n{e}")
