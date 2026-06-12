# DocToMarkdownCoreLib
DocToMarkdownCoreLib is built using [Core-Lib](https://github.com/shay-te/core-lib).

## Example

```python
import hydra
from doc_to_markdown_core_lib import DocToMarkdownCoreLib

hydra.core.global_hydra.GlobalHydra.instance().clear()
hydra.initialize(config_path='../../doc_to_markdown_core_lib/config')

# Create a new DocToMarkdownCoreLib using hydra (https://hydra.cc/docs/next/advanced/compose_api/) config
doc_to_markdown_core_lib = DocToMarkdownCoreLib(hydra.compose('doc_to_markdown_core_lib.yaml'))
# function_call
```

## License
Core-Lib in licenced under [MIT](https://github.com/shay-te/core-lib/blob/master/LICENSE)
