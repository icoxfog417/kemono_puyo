// constants
var IMAGE_SIZE = 100;
var CANVAS_WIDTH = 800;

// module aliases
var Engine = Matter.Engine,
Render = Matter.Render,
World = Matter.World,
Body = Matter.Body,
Bodies = Matter.Bodies;

// create an engine
var engine = Engine.create();
var render = Render.create({
    element: document.getElementById("canvas"),
    engine: engine,
    options: {
        width: CANVAS_WIDTH,
        height: 600,
        wireframes: false,
        background: '#fff'
    }
});

var boxA = Bodies.rectangle(400, 200, 80, 80);
var boxB = Bodies.rectangle(450, 50, 80, 80);
var ground = Bodies.rectangle(400, 610, 810, 30, { isStatic: true });

// add all of the bodies to the world
World.add(engine.world, [boxA, boxB, ground]);

// run the engine
Engine.run(engine);

// run the renderer
Render.run(render);

Vue.component("kemono-template", {
    delimiters: ["[[", "]]"],
    props: ["f"],
    template: "#kemono-template"
});


Vue.config.debug = true;
var app = new Vue({
    el: "#app",
    delimiters: ["[[", "]]"],
    data: {
        socket: null,
        friends: {},
        TANOSHII: 3
    },
    created: function(){
        var url = "ws://" + location.host + "/connect";
        this.socket = new ReconnectingWebSocket(url);
        var self = this;
        this.socket.onmessage = function(event) {
            var data = JSON.parse(event.data).data;
            self.push_friend(data);
        }
        CACHE.forEach(function(element) {
            setTimeout(function(){
                self.push_friend(element);
            }, Math.random() * 2000);
        });
    },
    methods: {
        push_friend: function(file_name_and_name){
            var file_name = file_name_and_name[0]
            var name = file_name_and_name[1]            
            var body = Bodies.circle(IMAGE_SIZE, IMAGE_SIZE, 60, {
                density: 0.0005,
                frictionAir: 0.06,
                restitution: 0.5,
                friction: 0.01,
                render: {
                    sprite: {
                        texture: "/static/_images/" + file_name
                    }
                },
                timeScale: 1.5
            })
            var x = parseInt(Math.random() * (CANVAS_WIDTH - IMAGE_SIZE)) + IMAGE_SIZE;            
            Body.setPosition(body, { x: x, y: 0 });
            World.add(engine.world, [body]);

            if(name in this.friends){
                this.friends[name].push(body)
            }else{
                this.friends[name] = [body]
            }
            setTimeout(function(){
                app.say(name);
            }, Math.random() * 1000);
            this.say(name);
            setTimeout(function(){
                app.tanoshii();                
            }, 2500);

        },
        say: function(name){
            var audio = new Audio("");
            var presets = ["cat", "dog", "tanoshii"];
            var _name = name;
            if(presets.indexOf(name) < 0){
                _name = "unknown";
            }
            var file_path = "/static/audio/" + _name + ".mp3";
            audio.src = file_path;
            setTimeout(function(){
                console.log(audio.src);
                audio.play();
            }, 1000);
        },
        tanoshii: function(){
            for(k in this.friends){
                if(this.friends[k].length >= this.TANOSHII){
                    var removeds = this.friends[k].splice(0, this.TANOSHII);
                    Matter.World.remove(engine.world, removeds);                    
                    this.say("tanoshii");
                }
            }
        }
    }
})
