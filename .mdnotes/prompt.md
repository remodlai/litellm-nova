

class SignaturePromptGenerator(dspy.Signature):
    f"""
    You will receive a natural language task description that leverages Remodl's Semantic DSL semantic keywords and statements.
    You will generate a compliant DSPy signature prompt and AiFunctionSchema.
    ***CRITICAL***


    when generating the ai_function_schema, all left side must be a valid python variable name and typed. The right side must be a valid dspy.InputField or dspy.OutputField:
    Good examples:

    
    Bad examples:
    - question = dspy.InputField()
    - question = dspy.InputField(desc="The question to refine")
    - refined_question = dspy.OutputField()
    - refined_question = dspy.OutputField(desc="The refined question")
    
   
    ### Semantic Keywords
    {keywords_formatted}

    ### Semantic Statements
    {statements_formatted}

    ### AI Function Schema
    {{ai_function_schema}}


    ### Correct DSPy Signature Format
    CORRECT DSPy SIGNATURE FORMAT:

    class ClassName(dspy.Signature): # required
    \\\"\\\"\\\"Instructions for the signature.\\\"\\\"\\\"
    
    field_name: type = dspy.InputField()
    field_name: type = dspy.InputField(desc="optional description")
    field_name: type = dspy.OutputField()
    field_name: type = dspy.OutputField(desc="optional description")

    CRITICAL RULES:
    1. Must inherit from 'dspy.Signature' (never just 'Signature')
    2. Docstring is brief and describes the task
    3. Use 'desc' parameter, NOT 'description'
    4. NO comments like "# Input fields" or "# Output fields"
    5. Type annotation BEFORE the = sign
    6. Format: field_name: type = dspy.InputField(desc="...")
    """