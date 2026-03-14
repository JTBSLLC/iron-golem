package io.irongolem;

import net.minecraft.gametest.framework.GameTestHelper;

public final class IronGolem {

    private IronGolem() {
    }

    public static TestContext wrap(GameTestHelper helper) {
        return new TestContext(helper);
    }
}
