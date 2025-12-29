import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js?module';
import { Capsule } from 'https://unpkg.com/three@0.160.0/examples/jsm/math/Capsule.js?module';
import { Octree } from 'https://unpkg.com/three@0.160.0/examples/jsm/math/Octree.js?module';


const GameState = { MENU: "menu", SETTINGS: "settings", PLAYING: "playing" };
const settingsScreen = document.getElementById("settingsScreen");
const settingsButton = document.getElementById("settingsButton");
const closeSettingsBtn = document.getElementById("closeSettings");
const sensInput = document.getElementById("sensInput");
const strafeToggle = document.getElementById("strafeToggle");
const startScreen = document.getElementById("startScreen");
const startButton = document.getElementById("startButton");
const usernameInput = document.getElementById("usernameInput");
const yawtextel = document.getElementById("yawtext");
const posxel = document.getElementById("posx");
const posyel = document.getElementById("posy");
const poszel = document.getElementById("posz");
const usernameHud = document.getElementById("usernameHud");
const pyodideStatusEl = document.getElementById("pyodideStatus");
const fpsCounterEl = document.getElementById("fpsCounter");
const bar = document.getElementById("bar");
const tabButtons = document.querySelectorAll(".tabButton");
const tabContents = document.querySelectorAll(".tabContent");
const labels = document.getElementsByClassName("label");
const savedStrafeSetting = localStorage.getItem("useStrafeInsteadOfTurn");
const raycaster = new THREE.Raycaster();
const placementRange = 8.0; // max distance from player
const placeableSurfaces = [];
const placedBlocks = [];


let lastCompassIndex = -1;
let fpsFrameCount = 0;
let fpsLastTime = performance.now();
let fpsValue = 0;
let gameStarted = false;
let playerName = "Player";
let mouseSensitivity = 0.002;
let currentState = GameState.MENU;
let previousState = null;
let useStrafeInsteadOfTurn = false; // default behavior
let pointerLockActive = false;

tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
        tabButtons.forEach(b => b.classList.remove("active"));
        tabContents.forEach(c => c.classList.remove("active"));

        btn.classList.add("active");
        document.getElementById(btn.dataset.tab).classList.add("active");
    });
});

useStrafeInsteadOfTurn = savedStrafeSetting === "true";
strafeToggle.checked = useStrafeInsteadOfTurn;
bar.style.width = `${5000}px`; // this must be arbitrarily wide so that the compass isn't squished

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1e1e1e);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

scene.add(new THREE.AmbientLight(0xffffff, 0.4));
const dirLight = new THREE.DirectionalLight(0xffffff, 1);
dirLight.position.set(5, 10, 5);
scene.add(dirLight);

const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);


function getPlacementTargetHybrid() {
    // Step 1: ray from camera through reticule
    raycaster.setFromCamera(new THREE.Vector2(0, 0), camera);
    const hits = raycaster.intersectObjects(placeableSurfaces, false);
    if (hits.length === 0) return null;

    const hit = hits[0];

    // Step 2: check distance from avatar
    const avatarPos = playerCapsule.start.clone();
    const dist = hit.point.distanceTo(avatarPos);

    if (dist > placementRange) {
        console.log("Too far from player:", dist.toFixed(2));
        return null;
    }
    else { console.log("that is acceptable (within distance)") }

    console.log("Placement hit at:", hit.point, "distance from avatar:", dist.toFixed(2));
    return hit;
}


function snapToGrid(position, normal) {
    const snapped = position.clone()
        .add(normal.multiplyScalar(0.5)) // move outward from surface
        .floor()
        .addScalar(0.5); // center of block

    // Always place at minimum ground height if below
    if (snapped.y < 0.5) snapped.y = 0.5; // floor + half block

    return snapped;
}


function placeBlock(position) {
    const block = new THREE.Mesh(
        new THREE.BoxGeometry(1, 1, 1),
        new THREE.MeshStandardMaterial({ color: 0x8888ff })
    );

    block.position.copy(position);
    scene.add(block);

    placedBlocks.push(block);
    placeableSurfaces.push(block);

    worldOctree.fromGraphNode(block); // just add this block
}


function rebuildOctree() {
    worldOctree.clear(); // completely remove old data
    if (ground) worldOctree.fromGraphNode(ground);
    placedBlocks.forEach(block => worldOctree.fromGraphNode(block));
}



function removeBlock(block) {
    // Remove from scene & arrays
    scene.remove(block);

    const i1 = placedBlocks.indexOf(block);
    if (i1 !== -1) placedBlocks.splice(i1, 1);

    const i2 = placeableSurfaces.indexOf(block);
    if (i2 !== -1) placeableSurfaces.splice(i2, 1);

    // Rebuild octree so the removed block is no longer collidable
    rebuildOctree();
}


function createSceneObjects() {
    // Ground and grid
    const ground = new THREE.Mesh(
        new THREE.PlaneGeometry(400, 400),
        new THREE.MeshStandardMaterial({
            color: 0x444444,
            side: THREE.DoubleSide
        })
    );
    ground.rotation.x = -Math.PI / 2;
    scene.add(ground);
    placeableSurfaces.push(ground);
    const grid = new THREE.GridHelper(400, 400);
    scene.add(grid);

    function createPineTree(x, y, z) {
        const tree = new THREE.Group();
        const trunkGeometry = new THREE.CylinderGeometry(0.15, 0.2, 2, 8);
        const trunkMaterial = new THREE.MeshStandardMaterial({ color: 0x8b5a2b });
        const trunk = new THREE.Mesh(trunkGeometry, trunkMaterial);
        trunk.position.y = 5;
        tree.add(trunk);
        const foliageMaterial = new THREE.MeshStandardMaterial({ color: 0x0b6623 });
        const cone1 = new THREE.Mesh(new THREE.ConeGeometry(1.2, 2, 8), foliageMaterial);
        cone1.position.y = 10;
        const cone2 = new THREE.Mesh(new THREE.ConeGeometry(1.0, 1.8, 8), foliageMaterial);
        cone2.position.y = 15;
        const cone3 = new THREE.Mesh(new THREE.ConeGeometry(0.8, 1.5, 8), foliageMaterial);
        cone3.position.y = 20;
        tree.add(cone1, cone2, cone3);
        tree.position.set(x, y, z);
        scene.add(tree);
    }

    function maketreegroup() {
        createPineTree(10, 0, -11);
        createPineTree(10, 0, -12);
        createPineTree(10, 0, -13);
        createPineTree(10, 0, -14);
        createPineTree(10, 0, -15);
        createPineTree(10, 0, -16);
        createPineTree(10, 0, -17);
        createPineTree(10, 0, -18);
        createPineTree(10, 0, -19);
        createPineTree(10, 0, -20);
        createPineTree(10, 0, -21);
        createPineTree(10, 0, -22);
        createPineTree(10, 0, -23);
        createPineTree(10, 0, -24);
        createPineTree(10, 0, -25);
        createPineTree(10, 0, -26);
    }


    function init_em_energy() {
        const amount = 100000;
        const positions = new Float32Array(amount * 3);
        const colors = new Float32Array(amount * 3);
        const sizes = new Float32Array(amount);
        const color = new THREE.Color(0xffffff);
        // SLAB dimensions (world units)
        const SLAB_WIDTH = 50;   // X
        const SLAB_HEIGHT = 5;   // Y (thin)
        const SLAB_DEPTH = 50;   // Z

        for (let i = 0; i < amount; i++) {
            // Uniform random distribution inside a box
            const x = Math.random() * SLAB_WIDTH;
            const y = Math.random() * SLAB_HEIGHT;
            const z = Math.random() * SLAB_DEPTH;
            const idx = i * 3;
            positions[idx] = x;
            positions[idx + 1] = y;
            positions[idx + 2] = z;
            color.setHSL(0.55, 0.7, 0.5);
            color.toArray(colors, idx);
            sizes[i] = 0.5;
        }

        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geometry.setAttribute('customColor', new THREE.BufferAttribute(colors, 3));
        geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

        const material = new THREE.ShaderMaterial({
            uniforms: {
                color: { value: new THREE.Color(0xffffff) },
                pointTexture: { value: new THREE.TextureLoader().load('assets/whitecircle.png') }
            },
            vertexShader: document.getElementById('vertexshader').textContent,
            fragmentShader: document.getElementById('fragmentshader').textContent,
            blending: THREE.AdditiveBlending,
            depthTest: true,
            depthWrite: false,
            transparent: true
        });

        const em_energy = new THREE.Points(geometry, material);
        scene.add(em_energy);
        return em_energy;
    }

    const em_energy = init_em_energy();
    const haloGeometry = new THREE.TorusGeometry(25, 1, 8, 100);
    const haloMaterial = new THREE.MeshBasicMaterial({ color: 0xffff00, wireframe: true });
    const halo = new THREE.Mesh(haloGeometry, haloMaterial);
    halo.position.set(0, 40, 0);
    halo.rotation.x = Math.PI / 2;
    scene.add(halo);
    const cubeMaterialred = new THREE.MeshStandardMaterial({ color: 0xff0000 });
    const cubeMaterialgreen = new THREE.MeshStandardMaterial({ color: 0xff80 });
    const cubeMaterialblue = new THREE.MeshStandardMaterial({ color: 0xff });
    const cubeMaterialgold = new THREE.MeshStandardMaterial({ color: 0xffff00 });

    const largeCube = new THREE.Mesh(new THREE.BoxGeometry(5, 20, 5), cubeMaterialgold);
    largeCube.position.set(20, 10, 10);
    scene.add(largeCube);

    const camtargcube = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.2, 0.2), cubeMaterialred);
    scene.add(camtargcube);

    function makestairs(
        scene,
        startX, startY, startZ,
        direction,
        numStairs,
        width,
        material
    ) {
        const RISE = 0.6;
        const RUN = 1.0;
        const PLATFORM_MULTIPLIER = 4;
        const directions = {
            N: { x: 0, z: -1 },
            S: { x: 0, z: 1 },
            E: { x: 1, z: 0 },
            W: { x: -1, z: 0 }
        };

        if (!directions[direction]) {
            throw new Error("Direction must be 'N', 'S', 'E', or 'W'");
        }

        const { x: dx, z: dz } = directions[direction];

        for (let i = 0; i < numStairs; i++) {
            const isLast = i === numStairs - 1;
            const height = RISE;
            const depth = isLast ? RUN * PLATFORM_MULTIPLIER : RUN;

            let stepWidthX, stepDepthZ;

            if (direction === "N" || direction === "S") {
                stepWidthX = width;
                stepDepthZ = depth;
            } else {
                stepWidthX = depth;
                stepDepthZ = width;
            }

            const geometry = new THREE.BoxGeometry(stepWidthX, height, stepDepthZ);
            const step = new THREE.Mesh(geometry, material);
            const depthOffset = isLast ? (depth - RUN) / 2 : 0;
            step.position.set(
                startX + dx * (RUN * i + depthOffset),
                startY + RISE * i + height / 2,
                startZ + dz * (RUN * i + depthOffset)
            );
            scene.add(step);
        }
    }

    maketreegroup()
    makestairs(scene, -12, 0, 6, "E", 67, 3, cubeMaterialred)
    // makestairs(scene, .5, 0, -18.5, "E", 17, 3, cubeMaterialgreen)
    // makestairs(scene, 19.5, 0, -18.5, "W", 17, 3, cubeMaterialgreen)

    // Player avatar (visual only)
    const bodyHeight = 4.0;
    const bodyRadius = 1.3;
    const headRadius = 1.2;
    const bodyMaterial = new THREE.MeshStandardMaterial({ color: 0x00ff00 });
    const headMaterial = new THREE.MeshStandardMaterial({ color: 0xffff00 });
    const body = new THREE.Mesh(
        new THREE.CapsuleGeometry(bodyRadius, bodyHeight, 4, 8),
        bodyMaterial
    );

    const head = new THREE.Mesh(
        new THREE.SphereGeometry(headRadius, 16, 16), headMaterial);
    body.position.y = bodyHeight / 2;
    head.position.y = bodyHeight + headRadius;
    const playerAxes = new THREE.AxesHelper(2); // length in units
    scene.add(playerAxes);
    const avatar = new THREE.Group();
    avatar.add(body);
    avatar.add(head);
    scene.add(avatar);

    return [bodyRadius, bodyHeight, avatar, camtargcube, em_energy, playerAxes, ground];
}

const [bodyRadius, bodyHeight, avatar, camtargcube, em_energy, playerAxes, ground] = createSceneObjects();
const worldOctree = new Octree();
worldOctree.fromGraphNode(ground); // add ground initially
worldOctree.fromGraphNode(scene);
const playerCapsule = new Capsule(
    new THREE.Vector3(0, bodyRadius, 0),    // location of collider feet 
    new THREE.Vector3(0, bodyHeight + bodyRadius, 0),    //    location of collider head 
    bodyRadius
);

// Input
const keys = {};
let yaw = 0;
let pitch = Math.PI / 4;
let firstPerson = false;
const UP_LOOK_THRESHOLD = -Math.PI / 24;
let isRunning = false;

// Movement & Physics
const velocity = new THREE.Vector3();
const direction = new THREE.Vector3();
const GRAVITY = 30;
const SPEED = 8;
const JUMP = 30;
let onGround = false;

async function loadPyodideInBackground() {
    try {
        const script = document.createElement("script");
        script.src = "https://cdn.jsdelivr.net/pyodide/v0.25.1/full/pyodide.js";
        script.async = true;
        document.head.appendChild(script);

        await new Promise((resolve, reject) => {
            script.onload = resolve;
            script.onerror = reject;
        });

        window.pyodide = await loadPyodide();
        await pyodide.loadPackage("numpy");

        // ⬇️ Execute Python from separate script block
        const pyCode = document.getElementById("py-grid-script").textContent;
        await pyodide.runPythonAsync(pyCode);

        // Extract grid
        const pyGrid = pyodide.globals.get("grid");
        window.scalarGrid = pyGrid.toJs({ copy: true });

        pyodideStatusEl.textContent = "Pyodide loaded";
        pyodideStatusEl.style.color = "#2ecc71";
    } catch (err) {
        console.error(err);
        pyodideStatusEl.textContent = "Pyodide failed";
        pyodideStatusEl.style.color = "#e74c3c";
    }
}


function updatePlayer(delta) {
    direction.set(0, 0, 0);
    if (keys['w']) direction.z -= 1;
    if (keys['s']) direction.z += 1;
    if (useStrafeInsteadOfTurn) {
        if (keys['a']) direction.x -= 1;
        if (keys['d']) direction.x += 1;
    } else {
        if (keys['a']) yaw += 0.07;
        if (keys['d']) yaw -= 0.07;
    }
    if (keys['i']) pitch -= 0.03;
    if (keys['j']) yaw += 0.03;
    if (keys['k']) pitch += 0.03;
    if (keys['l']) yaw -= 0.03;
    if (keys['i'] || keys['k']) {
        pitch = THREE.MathUtils.clamp(pitch, -Math.PI / 2 + 0.1, Math.PI / 2 - 0.1);
    }

    yaw = normalizeYaw(yaw);
    const currentSpeed = SPEED * (isRunning ? 2 : 1);
    direction.normalize();
    // Make w/a/s/d relative to camera view rather than static/absolute map directions
    direction.applyAxisAngle(new THREE.Vector3(0, 1, 0), yaw);
    velocity.x = direction.x * currentSpeed;
    velocity.z = direction.z * currentSpeed;

    if (onGround) {
        velocity.y = Math.max(0, velocity.y);
        if (keys[' ']) velocity.y = JUMP;
    } else {
        velocity.y -= GRAVITY * delta;
    }

    const deltaPos = velocity.clone().multiplyScalar(delta);
    playerCapsule.translate(deltaPos);

    const result = worldOctree.capsuleIntersect(playerCapsule);
    onGround = false;

    if (result) {
        playerCapsule.translate(result.normal.multiplyScalar(result.depth));
        onGround = result.normal.y > 0;

        // Snap small offsets on X/Z to nearest 0.01 to reduce jitter
        playerCapsule.start.x = Math.round(playerCapsule.start.x * 100) / 100;
        playerCapsule.start.z = Math.round(playerCapsule.start.z * 100) / 100;
    }

    if (result) {
        playerCapsule.translate(result.normal.multiplyScalar(result.depth));
        onGround = result.normal.y > 0;
    }

    avatar.position.copy(playerCapsule.start);
    avatar.rotation.y = yaw;
    playerAxes.position.copy(playerCapsule.start);
}


function normalizeYaw(yaw) {
    const TWO_PI = Math.PI * 2;
    return ((yaw % TWO_PI) + TWO_PI) % TWO_PI;
}


function updateCompass() {
    const degrees = THREE.MathUtils.radToDeg(yaw);
    const corrective_multiplier = 0.47;
    const labelwidth = window.innerWidth * 0.0588;
    const compwid = 8 * labelwidth;
    const x = degrees * corrective_multiplier * window.innerWidth / 360 - compwid;
    [...labels].map(z => z.style.width = `${labelwidth}px`);
    bar.style.left = x + "px";
}
window.addEventListener("resize", updateCompass);
updateCompass();


function updateCamera() {
    const isCameraInside = false;

    let cameraTarget = avatar.position.clone();

    if (isCameraInside) {
        cameraTarget.x += 0.8 * Math.cos(yaw);
        cameraTarget.z -= 0.8 * Math.sin(yaw);
        camera.position.copy(avatar.position);
    } else {
        const BASE_CAMERA_DISTANCE = 18;
        cameraTarget.x += 0.8 * Math.cos(yaw);
        cameraTarget.z -= 0.8 * Math.sin(yaw);
        cameraTarget.y += 1.7;
        camera.position.x = avatar.position.x - BASE_CAMERA_DISTANCE * Math.cos(yaw + Math.PI / 2) * Math.cos(pitch);
        camera.position.y = avatar.position.y + BASE_CAMERA_DISTANCE * Math.sin(pitch);
        camera.position.z = avatar.position.z + BASE_CAMERA_DISTANCE * Math.sin(yaw + Math.PI / 2) * Math.cos(pitch);
    }
    camtargcube.position.set(cameraTarget.x, cameraTarget.y, cameraTarget.z);
    camera.lookAt(cameraTarget);
}

function updateHUD() {
    const pos = playerCapsule.start;
    const yawDeg = (360 - THREE.MathUtils.radToDeg(yaw)) % 360;
    const yawRadNormalized = (2 * Math.PI - yaw) % (2 * Math.PI);
    yawtextel.textContent = `${yawRadNormalized.toFixed(3)} rad | ${((yawRadNormalized * 180 / Math.PI).toFixed(1))}°`;
    posxel.textContent = pos.x.toFixed(2);
    posyel.textContent = pos.y.toFixed(2);
    poszel.textContent = pos.z.toFixed(2);
    updateCompass();
}

function updateEMfield(time) {
    if (!window.scalarGrid) return; // Pyodide not ready yet

    const geometry = em_energy.geometry;
    const positions = geometry.attributes.position.array;
    const sizes = geometry.attributes.size.array;

    for (let i = 0; i < positions.length; i += 3) {
        const x = positions[i];
        const y = positions[i + 1];
        const z = positions[i + 2];
        const gsz = window.scalarGrid.length
        if (x < 0 || y < 0 || z < 0 || x > gsz || y > gsz || z > gsz) {
            sizes[i / 3] = 0;
        } else {
            const ix = Math.floor(x);
            const iy = Math.floor(y);
            const iz = Math.floor(z);
            const itime = Math.floor(time / 100) % 50

            // Read scalar value from Pyodide grid
            const scalar = window.scalarGrid[ix][iy][iz][itime];

            // Apply it to particle size
            sizes[i / 3] = scalar;
        }
    }
    geometry.attributes.size.needsUpdate = true;
}

let lastTime = performance.now();

function animate() {
    requestAnimationFrame(animate);
    if (currentState !== GameState.PLAYING) {
        renderer.render(scene, camera);
        return;
    }
    const time = performance.now();
    const deltaMs = time - lastTime;
    const delta = Math.min(0.03, deltaMs / 1000);
    lastTime = time;

    // FPS calculation
    fpsFrameCount++;
    if (time - fpsLastTime >= 500) { // update twice per second
        fpsValue = Math.round((fpsFrameCount * 1000) / (time - fpsLastTime));
        fpsCounterEl.textContent = fpsValue;
        fpsFrameCount = 0;
        fpsLastTime = time;
    }

    updatePlayer(delta);
    updateCamera();
    updateHUD();
    updateEMfield(time);
    renderer.render(scene, camera);
}

loadPyodideInBackground();
animate();

function setState(state) {
    previousState = currentState;
    currentState = state;
    startScreen.style.display =
        state === GameState.MENU ? "flex" : "none";
    settingsScreen.style.display =
        state === GameState.SETTINGS ? "flex" : "none";
    if (state === GameState.PLAYING) {
        document.body.requestPointerLock({ unadjustedMovement: true });
        document.body.style.cursor = "none";
    } else {
        document.exitPointerLock();
        document.body.style.cursor = "default";
    }
}

window.addEventListener("keydown", (e) => {
    keys[e.key.toLowerCase()] = true;
    if (e.key.toLowerCase() === "shift") isRunning = true;
    if (e.key.toLowerCase() === "v") firstPerson = !firstPerson;
    if (e.key === "Escape") {
        e.preventDefault();
        if (currentState === GameState.SETTINGS) { setState(previousState || GameState.MENU); }
    }
});

window.addEventListener('keyup', (e) => {
    keys[e.key.toLowerCase()] = false;
    if (e.key.toLowerCase() === 'shift') isRunning = false;
});

document.addEventListener("mousemove", (e) => {
    if (currentState !== GameState.PLAYING || document.pointerLockElement !== document.body
    ) return;
    yaw -= e.movementX * mouseSensitivity;
    yaw = normalizeYaw(yaw);
    pitch += e.movementY * mouseSensitivity;
    pitch = THREE.MathUtils.clamp(pitch, -Math.PI / 2 + 0.1, Math.PI / 2 - 0.1);
});

sensInput.addEventListener("input", e => {
    mouseSensitivity = parseFloat(e.target.value);
});

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

strafeToggle.addEventListener("change", e => {
    useStrafeInsteadOfTurn = e.target.checked;
    localStorage.setItem("useStrafeInsteadOfTurn", useStrafeInsteadOfTurn);
});

document.body.addEventListener("click", () => {
    if (currentState === GameState.PLAYING &&
        document.pointerLockElement !== document.body) {
        document.body.requestPointerLock({ unadjustedMovement: true });
    }
});

startButton.addEventListener("click", () => {
    playerName = usernameInput.value.trim() || "Player";
    usernameHud.textContent = `Player: ${playerName}`;
    gameStarted = true;
    setState(GameState.PLAYING);
});

settingsButton.addEventListener("click", () => {
    setState(GameState.SETTINGS);
});

closeSettingsBtn.addEventListener("click", () => {
    setState(previousState || GameState.MENU);
});

document.addEventListener("pointerlockchange", () => {
    const locked = document.pointerLockElement === document.body;
    pointerLockActive = locked;
    if (
        currentState === GameState.PLAYING && !locked
    ) {
        requestAnimationFrame(() => {
            if (currentState === GameState.PLAYING && !pointerLockActive
            ) {
                setState(GameState.SETTINGS);
            }
        });
    }
});

window.addEventListener("mousedown", (e) => {
    if (currentState !== GameState.PLAYING) return;
    if (document.pointerLockElement !== document.body) return;

    const hit = getPlacementTargetHybrid();
    if (!hit) return;

    // LEFT CLICK → place
    if (e.button === 0) {
        const placePos = snapToGrid(
            hit.point,
            hit.face.normal.clone()
        );
        placeBlock(placePos);
    }

    // RIGHT CLICK → remove
    if (e.button === 2) {
        const obj = hit.object;
        if (placedBlocks.includes(obj)) {
            scene.remove(obj);
            
            const i1 = placedBlocks.indexOf(obj);
            if (i1 !== -1) placedBlocks.splice(i1, 1);
            
            const i2 = placeableSurfaces.indexOf(obj);
            if (i2 !== -1) placeableSurfaces.splice(i2, 1);
        }
        removeBlock(obj)
    }
});

window.addEventListener("contextmenu", e => e.preventDefault());

