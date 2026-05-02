# 14 — Unity First-Run Verification Plan

## Purpose

Explain why we must open the LorQB-Android project in Unity **now**, before adding any more gameplay code.

---

## Context

The following core Unity scripts are now implemented and merged:

- `GameStateManager`
- `SequenceManager`
- `BallTransferController`
- `ValidationController`
- `InputController`
- `RotationController`
- `GameManager`
- `LevelCompletionController` *(disabled)*
- Transfer logging added

We need Unity verification before continuing because **GitHub only confirms that code exists**. Unity confirms that:

- The code **compiles**
- Components **attach** correctly
- References **wire** correctly
- Runtime **logs behave** correctly

---

## 1. Why Unity Now

| Reason | Detail |
|--------|--------|
| Prevent building on untested assumptions | New systems may depend on scripts that silently fail inside Unity |
| Catch compile errors early | A single namespace typo or missing `using` directive stops the entire project |
| Catch missing component/reference errors | `GetComponent<>()` calls that return `null` will crash at runtime, not at commit time |
| Confirm `GameManager` initializes all systems | `GameManager.Start()` must find and wire every required controller |
| Confirm `SequenceManager` generates sequence | The ball sequence must be non-null before any state transition runs |
| Confirm `GameStateManager` transitions to `BALL_SELECTION` | The opening state transition is the entry point for all gameplay |
| Confirm `BallTransferController` receives `SequenceManager` | Transfer logic depends on a valid sequence reference |
| Confirm validation/transfer logging is visible | Log output must appear in the Unity Console so future debugging is possible |

---

## 2. What Is NOT Being Tested Yet

- ❌ Android build
- ❌ Final graphics or art assets
- ❌ Blender asset import
- ❌ Real cube rotation gameplay
- ❌ Final touch controls

---

## 3. What IS Being Tested Now

- ✅ Project opens in Unity without errors
- ✅ All scripts compile successfully
- ✅ `GameManager` runs its initialization routine
- ✅ Console logs appear as expected
- ✅ State flow starts correctly (`→ BALL_SELECTION`)
- ✅ Transfer logging infrastructure can be triggered later

---

## 4. First-Run Checklist

1. [ ] Open **Unity Hub**
2. [ ] Click **Add** → select the `LorQB-Android` local project folder
3. [ ] Open the project in Unity
4. [ ] Wait for the full **import and compile** cycle to complete
5. [ ] Open the **Console** window (`Window → General → Console`)
6. [ ] Press **Play**
7. [ ] Confirm the following expected log lines appear:

```
[GameManager] Sequence generated.
[GameManager] State changed → BALL_SELECTION
```

---

## 5. Pass Condition

All of the following must be true for this verification to pass:

- ✅ No **red** Console errors
- ✅ Game enters `BALL_SELECTION` state
- ✅ All core systems compile without errors
- ✅ No missing namespace or missing component errors

---

## 6. Fail Condition

Verification fails if **any** of the following occur:

- 🔴 Red compiler errors in the Console
- 🔴 "Missing Script" errors on any GameObject
- 🔴 `GameStateManager.Instance` is `null` at runtime
- 🔴 `GameManager` cannot find one or more required components

---

## 7. Stop Rule

> **If any red error appears, stop coding immediately and fix the first error only.**

Do not stack new code on top of a broken foundation. Resolve errors one at a time, re-run the verification checklist, and confirm a clean Console before resuming development.

---

## Constraints

- 📄 Documentation only
- 🚫 Do not modify any C# scripts
- 🚫 Do not create Unity scenes
- 🚫 Do not change gameplay logic
