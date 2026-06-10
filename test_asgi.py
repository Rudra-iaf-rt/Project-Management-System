# test_asgi.py
async def application(scope, receive, send):
    if scope['type'] == 'http':
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [(b'content-type', b'text/html')],
        })
        await send({
            'type': 'http.response.body',
            'body': b'<h1>Daphne is Working!</h1>',
        })