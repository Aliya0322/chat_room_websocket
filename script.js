const ws = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@trade');

function addText(res){
    $('#reply').append(`<li>${res}</li>`);
}

ws.onopen = ()=>{
    addText('Подключено');
}

ws.onclose = ()=>{
    addText('Выключено');
}

ws.onerror = (err)=>{
    addText(`'Ошибка:${err}'`);
}

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if(parseFloat(data.q)>0.001) {
        addText(`'Ответ:${event.data}'`);
        console.log(event);
    }
}

function sendMessage () {
    const message = $('#message').val();
    if(ws.readyState==WebSocket.OPEN && message) {
        ws.send(message);
        $('#message').val('');
        addText("Отправлено");
    }
}

$('#message-btn').on('click', function () {
    console.log('Hello');
    sendMessage();
})