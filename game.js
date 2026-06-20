import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.164/build/three.module.js";

import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';

// Scene Setup
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x87ceeb); // Sky blue
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(ambientLight);
const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
directionalLight.position.set(10, 20, 10);
scene.add(directionalLight);

// Controls & Physics Vars
const controls = new PointerLockControls(camera, document.body);
const instructions = document.getElementById('instructions');
instructions.addEventListener('click', () => controls.lock());
controls.addEventListener('lock', () => instructions.style.display = 'none');
controls.addEventListener('unlock', () => instructions.style.display = 'block');

let moveForward = false, moveBackward = false, moveLeft = false, moveRight = false, canJump = false, isCrouching = false;
const velocity = new THREE.Vector3();
const direction = new THREE.Vector3();
const clock = new THREE.Clock();

// Objects
const blocks = new Map();
const boxGeometry = new THREE.BoxGeometry(1, 1, 1);
const floorGeometry = new THREE.PlaneGeometry(50, 50);
const floorMaterial = new THREE.MeshLambertMaterial({ color: 0x228b22 });
const floor = new THREE.Mesh(floorGeometry, floorMaterial);
floor.rotation.x = -Math.PI / 2;
scene.add(floor);

// Multiplayer
const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const socketUrl = isLocal 
    ? 'ws://localhost:8080' 
    : 'wss://your-unique-app-name.onrender.com'; // <--- REPLACE THIS after deploying

const socket = new WebSocket(socketUrl);
socket.onopen = () => console.log("Connected to live multiplayer!");
socket.onerror = () => {
    console.warn("Multiplayer server offline. Running in Single Player mode.");
    instructions.querySelector('h1').innerText = "Single Player Mode";
};

const remotePlayers = new Map();
const clientId = Math.random().toString(36).substring(7);

socket.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id === clientId) return;

    if (msg.type === 'pos') {
        if (!remotePlayers.has(msg.id)) {
            const p = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshLambertMaterial({ color: 0xffa500 }));
            scene.add(p);
            remotePlayers.set(msg.id, p);
        }
        remotePlayers.get(msg.id).position.set(msg.x, msg.y, msg.z);
    } else if (msg.type === 'place') {
        addBlock(new THREE.Vector3(msg.x, msg.y, msg.z), false);
    } else if (msg.type === 'destroy') {
        removeBlock(new THREE.Vector3(msg.x, msg.y, msg.z), false);
    }
};

// Input Handlers
const onKeyDown = (event) => {
    switch (event.code) {
        case 'KeyW': moveForward = true; break;
        case 'KeyS': moveBackward = true; break;
        case 'KeyA': moveLeft = true; break;
        case 'KeyD': moveRight = true; break;
        case 'Space': if (canJump) velocity.y += 10; canJump = false; break;
        case 'ShiftLeft': isCrouching = true; camera.position.y -= 0.4; break;
    }
};
const onKeyUp = (event) => {
    switch (event.code) {
        case 'KeyW': moveForward = false; break;
        case 'KeyS': moveBackward = false; break;
        case 'KeyA': moveLeft = false; break;
        case 'KeyD': moveRight = false; break;
        case 'ShiftLeft': isCrouching = false; camera.position.y += 0.4; break;
    }
};
document.addEventListener('keydown', onKeyDown);
document.addEventListener('keyup', onKeyUp);

// Interaction
window.addEventListener('mousedown', (event) => {
    if (!controls.isLocked) return;
    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(new THREE.Vector2(0, 0), camera);
    const intersects = raycaster.intersectObjects(scene.children);

    if (intersects.length > 0) {
        const intersect = intersects[0];
        if (event.button === 0) { // Left Click - Place
            const pos = intersect.point.clone().add(intersect.face.normal.multiplyScalar(0.5)).round();
            addBlock(pos, true);
        } else if (event.button === 2 && intersect.object !== floor) { // Right Click - Break
            removeBlock(intersect.object.position, true);
        }
    }
});

function addBlock(pos, sync) {
    const key = `${pos.x},${pos.y},${pos.z}`;
    if (blocks.has(key)) return;
    const block = new THREE.Mesh(boxGeometry, new THREE.MeshLambertMaterial({ color: 0x808080 }));
    block.position.copy(pos);
    scene.add(block);
    blocks.set(key, block);
    if (sync && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'place', id: clientId, x: pos.x, y: pos.y, z: pos.z }));
    }
}

function removeBlock(pos, sync) {
    const key = `${pos.x},${pos.y},${pos.z}`;
    const block = blocks.get(key);
    if (block) {
        scene.remove(block);
        blocks.delete(key);
        if (sync && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: 'destroy', id: clientId, x: pos.x, y: pos.y, z: pos.z }));
        }
    }
}

// Game Loop
camera.position.y = 1.6;
let lastPosSend = 0;

function animate() {
    requestAnimationFrame(animate);
    const delta = clock.getDelta();

    if (controls.isLocked) {
        velocity.x -= velocity.x * 10.0 * delta;
        velocity.z -= velocity.z * 10.0 * delta;
        velocity.y -= 9.8 * 2.5 * delta; // Gravity

        direction.z = Number(moveForward) - Number(moveBackward);
        direction.x = Number(moveRight) - Number(moveLeft);
        direction.normalize();

        const speed = isCrouching ? 20.0 : 50.0;
        if (moveForward || moveBackward) velocity.z -= direction.z * speed * delta;
        if (moveLeft || moveRight) velocity.x -= direction.x * speed * delta;

        controls.moveRight(-velocity.x * delta);
        controls.moveForward(-velocity.z * delta);
        camera.position.y += (velocity.y * delta);

        if (camera.position.y < 1.6) {
            velocity.y = 0;
            camera.position.y = 1.6;
            canJump = true;
        }

        // Network Sync Position
        if (socket.readyState === WebSocket.OPEN && Date.now() - lastPosSend > 50) {
            socket.send(JSON.stringify({
                type: 'pos', id: clientId,
                x: camera.position.x, y: camera.position.y, z: camera.position.z
            }));
            lastPosSend = Date.now();
        }
    }
    renderer.render(scene, camera);
}
animate();

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});
