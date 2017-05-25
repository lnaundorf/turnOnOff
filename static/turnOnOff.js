var too = {
    serverStates: {
        0: {
            title: "Turn on",
            disabled: false,
            func: function(server_id) {
                too.executeFunction(server_id, "turnOn", 1);
            },
            styleClass: "btn-primary",
        },
        1: {
            title: "Turned on",
            func: null,
            styleClass: "btn-warning"
        },
        2: {
            title: "Turn off",
            func: function(server_id) {
                too.executeFunction(server_id, "turnOff", 3);
            },
            styleClass: "btn-danger"
        },
        3: {
            title: "Turned off",
            func: null,
            styleClass: "btn-warning"
        }
    },
    servers: {},
    executeFunction: function(server_id, name, success_state) {
        $.getJSON("/server/" + server_id + "/" + name, function(response) {
            if (response.success) {
                too.servers[server_id].state = success_state;
                too.updateView();
            } else {
                console.error("Error for response: ", response);
            }
        });
    },
    updateState: function() {
        $.getJSON("/status", function(response) {
            for (let i = 0; i < response.length; i++) {
                let server = response[i];
                too.servers[server.pimatic_id] = server;
            }
            too.updateView();
        });
    },
    updateView: function() {
        let contentDiv = $('#content');
        contentDiv.html('');
        for (id in too.servers) {
            contentDiv.append(too.createElementForServer(too.servers[id]));
        }
    },
    createElementForServer: function(server) {
        let serverElement = $('<div class="server"></div>');

        serverElement.append('<div class="server-state-bubble bubble_' + server.state + '"></div>');
        let link = '<a href="' + server.check_address + '" target="_blank">' + server.name + '</a>';
        serverElement.append('<div class="server-name">' + link + '</div>');
        serverElement.append(too.createButtonForServer(server));
        
        return serverElement;
    },
    createButtonForServer: function(server) {
        let state = too.serverStates[server.state];
        let button = $('<button id="button_' + server.pimatic_id + '" class="btn btn-lg ' + state.styleClass + '" type="button"></button>');
        button.prop("disabled", !state.func);
        button.html(state.title);
        if (state.func) {
            button.click(function() {
                state.func.call(this, server.pimatic_id);
            })
        }

        
        return button;
    },
}
