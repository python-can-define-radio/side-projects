import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js?module';
import { Capsule } from 'https://unpkg.com/three@0.160.0/examples/jsm/math/Capsule.js?module';
import { Octree } from 'https://unpkg.com/three@0.160.0/examples/jsm/math/Octree.js?module';


const GameState = { MENU: "menu", SETTINGS: "settings", PLAYING: "playing" };
const settingsScreen = document.getElementById("settingsScreen");
const settingsButton = document.getElementById("settingsButton");
const closeSettingsBtn = document.getElementById("closeSettings");
const sensInput = document.getElementById("sensInput");
const camerafarInput = document.getElementById("camerafarInput");
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
const placementRange = 10.0; // max distance from player
const placeableSurfaces = [];
const placedBlocks = [];
const MIN_CAMERA_DISTANCE = 1; // first-person close to head
const MAX_CAMERA_DISTANCE = 30; // normal third-person

let cameraDistance = 4;      // starting third-person distance
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

const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 300);

const faceHighlight = new THREE.Mesh(
    new THREE.PlaneGeometry(1.01, 1.01),
    new THREE.MeshBasicMaterial({
        color: 0xffff00,
        transparent: true,
        opacity: 0.35,
        side: THREE.DoubleSide,
        depthWrite: false
    })
);

faceHighlight.visible = false;
scene.add(faceHighlight);


function updateFaceHighlight() {
    const hit = getPlacementTargetHybrid();
    if (!hit || !hit.face) {
        faceHighlight.visible = false;
        return;
    }

    const normal = hit.face.normal.clone();

    // Transform normal to world space
    normal.transformDirection(hit.object.matrixWorld);

    // Snap position to 1x1 grid along the face
    const snappedPos = snapToFace(hit);
    faceHighlight.position.copy(snappedPos);

    // Orient plane so its local +Z points along the face normal
    const targetNormal = normal.clone().normalize();
    const currentNormal = new THREE.Vector3(0, 0, 1); // plane default normal
    const quaternion = new THREE.Quaternion().setFromUnitVectors(currentNormal, targetNormal);
    faceHighlight.quaternion.copy(quaternion);

    // Always scale 1x1
    faceHighlight.scale.set(1, 1, 1);

    faceHighlight.visible = true;
}


/**
 * Attempts to find a valid placement target by casting a ray from the camera
 * through the reticule and checking intersection with placeable surfaces.
 * @returns {THREE.Intersection|null} The closest valid intersection hit, or null if none found
 */
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
    } else {
        console.log("that is acceptable (within distance)");
    }

    console.log("Placement hit at:", hit.point, "distance from avatar:", dist.toFixed(2));
    return hit;
}


function snapToFace(hit) {
    const pos = hit.point.clone();
    const normal = hit.face.normal.clone();

    // Check if the object is the ground (or a non-cube plane)
    const isPlane = hit.object === ground; // or use some tag for all planes

    if (isPlane) {
        // Snap to 1x1 grid on X/Z only, keep Y fixed to surface
        const facePos = new THREE.Vector3(
            Math.floor(pos.x) + 0.5,
            pos.y + 0.01,  // tiny offset to avoid z-fighting
            Math.floor(pos.z) + 0.5
        );
        return facePos;
    }

    // --- Cube logic for blocks ---
    const cubeCenter = pos.clone().floor().addScalar(0.5);

    if (normal.x > 0) cubeCenter.x -= 1;
    if (normal.y > 0) cubeCenter.y -= 1;
    if (normal.z > 0) cubeCenter.z -= 1;

    const facePos = cubeCenter.addScaledVector(normal, 0.5);
    facePos.addScaledVector(normal, 0.01); // small offset
    return facePos;
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


class InstancedPool {
    /**
     * @param {THREE.Scene} scene - The scene to add the instanced mesh into
     * @param {THREE.BufferGeometry} geometry - Geometry for each instance
     * @param {THREE.Material} material - Material for each instance
     * @param {number} count - Maximum number of instances
     */
    constructor(scene, geometry, material, count) {
        this.mesh = new THREE.InstancedMesh(geometry, material, count);
        scene.add(this.mesh);

        this.capacity = count;
        this.freeIndices = Array.from({ length: count }, (_, i) => i);
        this.active = new Map(); // key = "x,y,z" string, value = index
        this.dummy = new THREE.Object3D();
    }

    /**
     * Add a cube at the given coordinates.
     * @param {number} x
     * @param {number} y
     * @param {number} z
     * @returns {string|null} id - The coordinate key for later removal, or null if pool is full
     */
    add(x, y, z) {
        if (this.freeIndices.length === 0) return null;

        const index = this.freeIndices.pop();
        this.dummy.position.set(x, y, z);
        this.dummy.rotation.set(0, 0, 0);
        this.dummy.scale.set(1, 1, 1);
        this.dummy.updateMatrix();

        this.mesh.setMatrixAt(index, this.dummy.matrix);
        this.mesh.instanceMatrix.needsUpdate = true;

        const id = `${x},${y},${z}`; // use coordinates as the id
        this.active.set(id, index);
        return id;
    }

    /**
     * Remove a cube at the given coordinates.
     * @param {number} x
     * @param {number} y
     * @param {number} z
     * @returns {boolean} true if removed, false if not found
     */
    remove(x, y, z) {
        const id = `${x},${y},${z}`;
        if (!this.active.has(id)) return false;

        const index = this.active.get(id);
        this.active.delete(id);
        this.freeIndices.push(index);

        // Hide it by scaling to zero
        this.dummy.position.set(0, 0, 0);
        this.dummy.scale.set(0, 0, 0);
        this.dummy.updateMatrix();
        this.mesh.setMatrixAt(index, this.dummy.matrix);
        this.mesh.instanceMatrix.needsUpdate = true;

        return true;
    }
}


function placeBlock(position) {
    pool.add(position.x, position.y, position.z);

    // placedBlocks.push(block);
    // placeableSurfaces.push(block);

    // worldOctree.fromGraphNode(block); // just add this block
}


function rebuildOctree() {
    worldOctree.clear(); // completely remove old data
    if (ground) worldOctree.fromGraphNode(ground);
    placedBlocks.forEach(block => worldOctree.fromGraphNode(block));
}


function removeBlock(block) {
    if (block === ground) return;
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
        const SLAB_WIDTH = 100;   // X
        const SLAB_HEIGHT = 2;   // Y (thin)
        const SLAB_DEPTH = 100;   // Z

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
    largeCube.position.set(70, 10, 10);
    scene.add(largeCube);

    const camtargcube = new THREE.Mesh(new THREE.BoxGeometry(.7, .7, .7), cubeMaterialred);
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
    const avscale = 0.2;
    const bodyHeight = 4.0 * avscale;
    const bodyRadius = 1.3 * avscale;
    const headRadius = 1.2 * avscale;
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
    const playerAxes = new THREE.AxesHelper(1); // length in units
    scene.add(playerAxes);
    const avatar = new THREE.Group();
    avatar.add(body);
    avatar.add(head);
    scene.add(avatar);

    return [bodyRadius, bodyHeight, avatar, camtargcube, em_energy, playerAxes, ground];
}

const [bodyRadius, bodyHeight, avatar, camtargcube, em_energy, playerAxes, ground] = createSceneObjects();

const pool = new InstancedPool(
    scene,
    new THREE.BoxGeometry(1, 1, 1),
    new THREE.MeshNormalMaterial(),
    100000
);
pool.mesh.frustumCulled = false;

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
const SPEED = 12;
const JUMP = 20;
let onGround = false;


async function loadPythonFile(path) {
    const response = await fetch(path);
    if (!response.ok) {
        throw new Error(`Failed to load Python file: ${path}`);
    }
    return await response.text();
}


async function loadPyodideInBackground() {
    pyodideStatusEl.textContent = "Pyodide SKIPPEDEDEDDD";    
    return;  // 2026 jan 16: disabled this
    
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

        // 🔥 Load external Python file
        const pyCode = await loadPythonFile("__insert_game_name_here__.py");
        await pyodide.runPythonAsync(pyCode);

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
    if (keys['w']) direction.z += 1;
    if (keys['s']) direction.z -= 1;
    if (useStrafeInsteadOfTurn) {
        if (keys['a']) direction.x += 1;
        if (keys['d']) direction.x -= 1;
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

    if (keys[' ']) velocity.y = JUMP;
    if (onGround) {
        velocity.y = Math.max(0, velocity.y);
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
    const cameraTarget = avatar.position.clone();
    cameraTarget.y += bodyHeight * 1.8;

    const dist = cameraDistance || 30;

    camera.position.x = cameraTarget.x - dist * Math.sin(yaw) * Math.cos(pitch);
    camera.position.y = cameraTarget.y + dist * Math.sin(pitch);
    camera.position.z = cameraTarget.z - dist * Math.cos(yaw) * Math.cos(pitch);

    camera.lookAt(cameraTarget);

    // Fade avatar smoothly
    const fadeStart = 2; // start fading when closer than this
    const fadeEnd = 1;   // fully invisible at this distance
    let opacity = 1;
    if (dist <= fadeStart) {
        opacity = THREE.MathUtils.clamp((dist - fadeEnd) / (fadeStart - fadeEnd), 0, 1);
    }

    // Traverse all meshes in avatar and force opacity
    avatar.traverse((child) => {
        if (child.isMesh) {
            // Ensure a **unique material instance** for each mesh
            if (!child.material._originalMaterial) {
                child.material = child.material.clone();
                child.material._originalMaterial = true;
            }

            child.material.transparent = true;
            child.material.opacity = opacity;

            // Optional: disable depthWrite for complete fade
            // child.material.depthWrite = opacity > 0 ? true : false;
        }
    });
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
    // try {
    if (!window.scalarGrid) return; // Pyodide not ready yet
    const geometry = em_energy.geometry;
    const positions = geometry.attributes.position.array;
    const sizes = geometry.attributes.size.array;

    for (let i = 0; i < positions.length; i += 3) {
        const x = positions[i];
        const y = positions[i + 1];
        const z = positions[i + 2];
        const gs_time = window.scalarGrid.length;
        const gs_x = window.scalarGrid[0].length;
        const gs_y = window.scalarGrid[0][0].length;
        const gs_z = window.scalarGrid[0][0][0].length;
        if (x < 0 || y < 0 || z < 0 || x > gs_x || y > gs_y || z > gs_z) {
            sizes[i / 3] = 0;
        } else {
            const ix = Math.floor(x);
            const iy = Math.floor(y);
            const iz = Math.floor(z);
            const itime = Math.floor(time / 50) % gs_time;

            // Read scalar value from Pyodide grid
            const scalar = Math.max(0, -6 + 70 * Math.log(1 + Math.abs(scalarGrid[itime][ix][iy][iz])));
            // Apply it to particle size
            sizes[i / 3] = scalar;
        }
    }
    geometry.attributes.size.needsUpdate = true;
    // } catch (e) {
    //     console.log("error:");
    //     console.log(e);
    // }
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
    updateFaceHighlight();
    updateHUD();
    updateEMfield(time);
    renderer.render(scene, camera);
}

setTimeout(loadPyodideInBackground, 5000);
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

window.addEventListener("wheel", (e) => {
    if (currentState !== GameState.PLAYING) return;

    // Invert scroll if you want "scroll up to zoom in"
    cameraDistance += e.deltaY * 0.01;
    cameraDistance = THREE.MathUtils.clamp(cameraDistance, MIN_CAMERA_DISTANCE, MAX_CAMERA_DISTANCE);
});

sensInput.addEventListener("input", e => {
    mouseSensitivity = parseFloat(e.target.value);
});

camerafarInput.addEventListener("input", e => {
    camera.far = parseFloat(e.target.value);
    camera.updateProjectionMatrix();
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
        for (let countx = 0; countx < 200; countx++) {
            for (let countz = 0; countz < 500; countz++) {
                placeBlock(placePos);
                placePos.z += 2;
            }
            placePos.z -= 1000;
            placePos.x += 2;
        }
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

