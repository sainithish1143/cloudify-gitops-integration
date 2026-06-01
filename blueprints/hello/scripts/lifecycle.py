from cloudify import ctx


def _log_input_summary(action, customer_name, application_name, environment, message, replicas):
    ctx.logger.info("============================================================")
    ctx.logger.info("Cloudify GitOps desired-state demo lifecycle action: %s", action)
    ctx.logger.info("User-provided customer_name : %s", customer_name)
    ctx.logger.info("User-provided application   : %s", application_name)
    ctx.logger.info("User-provided environment   : %s", environment)
    ctx.logger.info("User-provided replicas      : %s", replicas)
    ctx.logger.info("User-provided message       : %s", message)
    ctx.logger.info("Deployment ID               : %s", ctx.deployment.id)
    ctx.logger.info("Node instance ID            : %s", ctx.instance.id)
    ctx.logger.info("============================================================")


_log_input_summary(
    action=ctx.operation.inputs.get("action", "unknown"),
    customer_name=ctx.operation.inputs.get("customer_name"),
    application_name=ctx.operation.inputs.get("application_name"),
    environment=ctx.operation.inputs.get("environment"),
    message=ctx.operation.inputs.get("message"),
    replicas=ctx.operation.inputs.get("replicas"),
)
