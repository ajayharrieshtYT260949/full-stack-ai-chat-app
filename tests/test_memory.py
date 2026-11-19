from app.services.memory_service import apply_sliding_window

def test_sliding_window_keeps_latest():
    history = [{"role":"user","content":str(i)} for i in range(8)]
    assert [x["content"] for x in apply_sliding_window(history, 3)] == ["5","6","7"]

def test_sliding_window_does_not_mutate_history():
    history = [{"role":"user","content":str(i)} for i in range(5)]
    apply_sliding_window(history, 2)
    assert len(history) == 5
