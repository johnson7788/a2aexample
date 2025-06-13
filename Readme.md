# 官方示例代码测试

# 安装方法
参考：
a2a-adk-app/README.md



## Bug  a2a-sdk的0.2.7版本报错，0.2.5可以正常
a2a-sdk==0.2.7

```bash
  File "/Users/yanbozhao/Documents/Doctor/DoctorPrograms/GOOGLEADK/a2aexample/A2Aclient.py", line 154, in completeTask
    taskResult = taskResult.root.result
                 ^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/anaconda3/envs/a2a/lib/python3.12/site-packages/pydantic/main.py", line 991, in __getattr__
    raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
AttributeError: 'JSONRPCErrorResponse' object has no attribute 'result'

Process finished with exit code 1
```

fastmcp==2.8.0会报错，使用fastmcp==2.2.5 
```bash
    报错
        result = text_check(userInput=user_input_text, Threshold=Threshold)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: 'FunctionTool' object is not callable
```