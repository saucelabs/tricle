# tricle

tricle is a python3 [monocle](http://github.com/saucelabs/monocle)
adapter, allowing monocle code ported from python2 to work with
minimal modifications, and to interoperate gracefully with python3's
native asyncio framework. It has two main goals:

1) Allow for a smooth, incremental transition away from monocle-based
code to native asyncio code.

2) Where monocle had significantly better ideas and APIs than are
available on asyncio, continue to refine those components to be useful
to all users of asyncio.

Monocle behaviors are copied closely, but not exactly — object APIs,
exceptions raised, and other details may differ in some cases. The
hope here is to make porting monocle code easy, but not necessarily
automatic. We want to encourage migration to native asyncio code, so
tricle at times tries to expose underlying asyncio APIs and mechanisms
rather than wrap them completely.  Some more essoteric monocle
functionality may not be copied, especially where asyncio alternatives
exist.

## Examples

Example interoperation with asyncio:

    # monocle oroutines work unmodified:
    @_o
    def slow_square(x):
        yield monocle.util.sleep(x)
        yield Return(x * x)

    # here's how to do something similar with asyncio and python3 async/await syntax:
    async slow_cube(x):
        await asyncio.sleep(x)
        return x * x * x
        
    # monocle oroutines can yield to native coroutines seamlessly:
    @_o
    def slow_sixth_power(x):
        yield asyncio.sleep(x)  # monocle.util.sleep is in fact this same function
        y = yield slow_cube(x * x)
        yield Return(y)
        
    # from native code, monocle oroutines can be awaited seamlessly:
    async def slow_fourth_power(x):
        y = await slow_square(x * x)
        return y

## Recommendations

When porting code from monocle to python3, these steps are recommended:

1) Run 2to3 on your code, and install tricle.

2) Run tests, and fix any bugs by replacing broken pieces with native
asyncio components. Always fix bugs by moving toward more native code.

3) Over time, rewrite oroutines to use native async/await syntax.

## Breaking Changes
Here is a list of breaking changes to consider when moving from monocle to tricle.
### HttpRequest.body_file
HttpRequest.body_file is now a bytes object.
If you have used `request.body_file.read()` to get a string in the past, you must now use `request.body_file.decode()`
instead. Another option is to use the convenience property `request.body`, which returns the body as string.