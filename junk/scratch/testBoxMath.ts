import assert from 'assert';
import { scaleBoundingBox } from './frontend/src/utils/boxMath.ts';

function runTests() {
  console.log("Running boxMath tests...");

  // Test 1: Direct 1-to-1 scale
  let res = scaleBoundingBox(
    10, 20, 30, 40,
    640, 480,
    640, 480,
    640, 480
  );
  assert.deepStrictEqual(res, [10, 20, 30, 40], "1-to-1 scaling failed");

  // Test 2: Scale up by 2x (exact aspect ratio)
  res = scaleBoundingBox(
    10, 20, 30, 40,
    640, 480,
    1280, 960,
    1280, 960
  );
  assert.deepStrictEqual(res, [20, 40, 60, 80], "2x exact scale failed");

  // Test 3: Letterboxing (canvas wider than video)
  // Analysis: 640x480
  // Canvas: 1000x480
  // Video intrinsic: 640x480
  // Video should be 640 wide, centered in 1000. So offset X is (1000-640)/2 = 180.
  // Box x=10 -> 10 + 180 = 190.
  res = scaleBoundingBox(
    10, 20, 30, 40,
    640, 480,
    1000, 480,
    640, 480
  );
  assert.deepStrictEqual(res, [190, 20, 210, 40], "Letterbox X scaling failed");

  // Test 4: Letterboxing (canvas taller than video)
  // Canvas 640x800
  // Video intrinsic 640x480
  // Offset Y = (800-480)/2 = 160.
  // Box y=20 -> 20 + 160 = 180.
  res = scaleBoundingBox(
    10, 20, 30, 40,
    640, 480,
    640, 800,
    640, 480
  );
  assert.deepStrictEqual(res, [10, 180, 30, 200], "Letterbox Y scaling failed");

  // Test 5: Clamping Out-of-bounds
  res = scaleBoundingBox(
    -100, -100, 1000, 1000,
    640, 480,
    640, 480,
    640, 480
  );
  assert.deepStrictEqual(res, [0, 0, 640, 480], "Clamping failed");

  console.log("All boxMath tests passed!");
}

runTests();
