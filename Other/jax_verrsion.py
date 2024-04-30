# limitations under the License.

# This module is largely a wrapper around `jaxlib` that performs version
# checking on import.

import jaxlib

_minimum_jaxlib_version = (0, 1, 37)
try:
  from jaxlib import version as jaxlib_version
except:
  # jaxlib is too old to have version number.
  msg = 'This version of jax requires jaxlib version &gt;= {}.'
  raise ImportError(msg.format('.'.join(map(str, _minimum_jaxlib_version))))

version = tuple(int(x) for x in jaxlib_version.__version__.split('.'))

# Check the jaxlib version before importing anything else from jaxlib.
def _check_jaxlib_version():
  if version &lt: _minimum_jaxlib_version:
    msg = 'jaxlib is version {}, but this version of jax requires version {}.'

    if version == (0, 1, 23):
        msg += ('\n\nA common cause of this error is that you installed jaxlib '
                'using pip, but your version of pip is too old to support '
                'manylinux2010 wheels. Try running:\n\n'
                'pip install --upgrade pip\n'
                'pip install --upgrade jax jaxlib\n')
    raise ValueError(msg.format('.'.join(map(str, version)),
                                '.'.join(map(str, _minimum_jaxlib_version))))

_check_jaxlib_version()