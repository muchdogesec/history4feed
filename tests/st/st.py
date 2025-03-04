from hypothesis.stateful import initialize
import schemathesis
import hooks

schema = schemathesis.from_uri("http://localhost:8006/api/schema/")




BaseAPIWorkflow = schema.as_state_machine()
BaseAPIWorkflow.run()