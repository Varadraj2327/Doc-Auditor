class EmailGenerator:
    def __init__(self, company_name="DocAuditor AI"):
        self.company_name = company_name

    def generate_compliance_alert(self, doc_name, errors, recipient="User"):
        subject = f"ACTION REQUIRED: Compliance Failure for {doc_name}"
        
        error_list = "\n".join([f"- {err}" for err in errors])
        
        body = f"""
Hello {recipient},

This is an automated alert from {self.company_name}.
Our AI system has detected compliance issues with the document you recently uploaded.

Document: {doc_name}
Status: FAILED

Detected Issues:
{error_list}

Please review the document and re-upload reaching the required compliance standards.

Regards,
{self.company_name} Compliance Team
        """
        return {"subject": subject, "body": body}
