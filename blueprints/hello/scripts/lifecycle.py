from cloudify import ctx


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _operation_values():
    """Return operation inputs/kwargs in a Cloudify-version tolerant way.

    Some Cloudify versions expose operation parameters via ctx.operation.inputs,
    while others expose them via ctx.operation.kwargs. This demo supports both
    and prefers kwargs because execute_operation passes operation_kwargs there.
    """
    values = {}

    operation = getattr(ctx, "operation", None)
    if operation is not None:
        values.update(_as_dict(getattr(operation, "inputs", None)))
        values.update(_as_dict(getattr(operation, "kwargs", None)))

    return values


def _get(values, key, default="N/A"):
    value = values.get(key, default)
    return default if value is None else value


values = _operation_values()

action = _get(values, "action", "workflow-operation")
customer_name = _get(values, "customer_name")
application_name = _get(values, "application_name")
environment = _get(values, "environment")
message = _get(values, "message")
replicas = _get(values, "replicas", 1)

ctx.logger.info("============================================================")
ctx.logger.info("Cloudify GitOps/Jenkins operation execution")
ctx.logger.info("Lifecycle action/workflow context : %s", action)
ctx.logger.info("Deployment ID                     : %s", ctx.deployment.id)
ctx.logger.info("Node ID                           : %s", ctx.node.id)
ctx.logger.info("Node instance ID                  : %s", ctx.instance.id)
ctx.logger.info("User input - customer_name        : %s", customer_name)
ctx.logger.info("User input - application_name     : %s", application_name)
ctx.logger.info("User input - environment          : %s", environment)
ctx.logger.info("User input - replicas             : %s", replicas)
ctx.logger.info("User input - message              : %s", message)
ctx.logger.info("============================================================")

ctx.instance.runtime_properties["customer_name"] = customer_name
ctx.instance.runtime_properties["application_name"] = application_name
ctx.instance.runtime_properties["environment"] = environment
ctx.instance.runtime_properties["replicas"] = replicas
ctx.instance.runtime_properties["message"] = message
ctx.instance.runtime_properties["last_action"] = action
ctx.logger.info("Runtime properties updated successfully")
