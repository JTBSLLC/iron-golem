package io.irongolem;

import net.minecraft.gametest.framework.GameTestHelper;

public class TestContext {

    private final GameTestHelper helper;

    public TestContext(GameTestHelper helper) {
        this.helper = helper;
    }

    public void placeBlock(int x, int y, int z, String blockId) {
    }

    public void breakBlock(int x, int y, int z) {
    }

    public void interactBlock(int x, int y, int z) {
    }

    public void insertItem(int x, int y, int z, int slot, String itemStack) {
    }

    public void tickFor(int ticks) {
        helper.runAfterDelay(ticks, helper::succeed);
    }

    public void assertBlockState(int x, int y, int z, String property, Object value) {
    }

    public void assertInventory(int x, int y, int z, int slot, Object matcher) {
    }

    public void succeed() {
        helper.succeed();
    }
}
