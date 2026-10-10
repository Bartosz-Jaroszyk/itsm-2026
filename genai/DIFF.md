---
lab3_genai_diff:
  instrumentation: "opentelemetry-instrumentation-genai-openai==1.2b0 (OpenAI Python SDK)"
  spec_ref: semantic-conventions@v1.41.1
  attributes:
    - {name: gen_ai.provider.name, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.operation.name, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.request.model, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.model, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.id, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.finish_reasons, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.usage.input_tokens, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.usage.output_tokens, emitted: true, in_spec: true, stability: development}
---
<!-- ai-generated: 90% - AI drafted an illustrative OTLP span and compared its GenAI attributes with semantic-conventions v1.41.1 -->
# What the instrumentation emits, against the spec

`spans.json` is a synthetic OpenTelemetry OTLP example for one successful OpenAI chat-completion call using
`gpt-4o-mini`. It illustrates the requested instrumentation's span shape; it is not a trace captured from a
running application. The listed attributes are exactly the `gen_ai.*` keys in that span.

All eight listed attributes are defined in `semantic-conventions@v1.41.1`, and each has `development` stability
in that registry. The example therefore shows agreement for these fields: the provider and operation identify the
call, the requested and responding model fields identify model selection, response metadata describes its result,
and the token-usage fields record the input and output counts. A dashboard can use these names to group or inspect
GenAI calls and token usage, but should treat them as development-stability conventions that may evolve.
