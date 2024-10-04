param($target,$test,$duration,$module,$atomic,$nameOptionOpt,$nameOptionVal,$user,$passwd,$cleanup,$inputArgs)
Import-Module $module -Force
$PSDefaultParameterValues = @{"Invoke-AtomicTest:PathToAtomicsFolder"="$atomic"};
Invoke-Expression 'netstat'
if ($null -ne $target){
    $sess = New-PSSession -HostName $target -UserName $user -KeyFilePath $passwd
    "\nTarget Port:22;"
    Invoke-Expression 'netstat'

    if($nameOptionOpt -eq "TestNames"){
        Invoke-AtomicTest $test -Session $sess -TestNames $nameOptionVal  -GetPrereqs
        Invoke-AtomicTest $test -Session $sess -TimeoutSecond $duration -TestNames $nameOptionVal -InputArgs $inputArgs
        if($null -ne $cleanup){
            Invoke-AtomicTest $test -Session $sess -TestNames $nameOptionVal -Cleanup
        }
    }elseif($nameOptionOpt -eq "TestNumbers"){
        Invoke-AtomicTest $test -Session $sess -TestNumbers $nameOptionVal -GetPrereqs
        Invoke-AtomicTest $test -Session $sess -TimeoutSecond $duration -TestNumber $nameOptionVal -InputArgs $inputArgs
        if($null -ne $cleanup){
            Invoke-AtomicTest $test -Session $sess -TestNumbers $nameOptionVal -Cleanup
        }
    }elseif($nameOptionOpt -eq "TestGuids"){
        Invoke-AtomicTest $test -Session $sess -TestGuids $nameOptionVal -GetPrereqs
        Invoke-AtomicTest $test -Session $sess -TimeoutSecond $duration -TestGuids $nameOptionVal -InputArgs $inputArgs
        if($null -ne $cleanup){
            Invoke-AtomicTest $test -Session $sess -TestGuids $nameOptionVal -Cleanup
        }
    }else{
        Invoke-AtomicTest $test -Session $sess -GetPrereqs        
        Invoke-AtomicTest $test -Session $sess -TimeoutSecond $duration -InputArgs $inputArgs
        if($null -ne $cleanup){
            Invoke-AtomicTest $test -Session $sess -Cleanup
        }
    }
    Remove-PSSession $sess.Id
}else{
    if($nameOptionOpt -eq "TestNames"){
        Invoke-AtomicTest $test -TestNames $nameOptionVal  -GetPrereqs
        Invoke-AtomicTest $test -TimeoutSecond $duration -TestNames $nameOptionVal -InputArgs $inputArgs
        if($null -ne $cleanup){
            Invoke-AtomicTest $test -TestNames $nameOptionVal -Cleanup
        }
    }elseif($nameOptionOpt -eq "TestNumbers"){
        Invoke-AtomicTest $test -TestNumbers $nameOptionVal -GetPrereqs
        Invoke-AtomicTest $test -TimeoutSecond $duration -TestNumber $nameOptionVal -InputArgs $inputArgs
        if($null -ne $cleanup){
            Invoke-AtomicTest $test  -TestNumbers $nameOptionVal -Cleanup
        }
    }elseif($nameOptionOpt -eq "TestGuids"){
        Invoke-AtomicTest $test -TestGuids $nameOptionVal -GetPrereqs
        Invoke-AtomicTest $test -TimeoutSecond $duration -TestGuids $nameOptionVal -InputArgs $inputArgs
        if($null -ne $cleanup){
            Invoke-AtomicTest $test -TestGuids $nameOptionVal -Cleanup
        }
    }else{
        Invoke-AtomicTest $test -GetPrereqs
        Invoke-AtomicTest $test -TimeoutSecond $duration -InputArgs $inputArgs
        if($null -ne $cleanup){
            Invoke-AtomicTest $test -Cleanup
        }
    }
}

"Done with pwsh script"