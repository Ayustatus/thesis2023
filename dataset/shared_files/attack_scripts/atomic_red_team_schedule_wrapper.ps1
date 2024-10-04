param($target,$schedule,$duration,$module,$atomic,$user,$passwd,$cleanup)
Import-Module $module -Force

$PSDefaultParameterValues = @{"Invoke-AtomicTest:PathToAtomicsFolder"="$atomic"};
Invoke-Expression "netstat"
if ($null -ne $target){
    $sess =  New-PSSession -HostName $target -UserName $user -KeyFilePath $passwd
    "\nTarget Port:22;"
    Invoke-Expression "netstat"
    Invoke-AtomicRunner -Session $sess -listOfAtomics $schedule -GetPrereqs
    Invoke-AtomicRunner -Session $sess -TimeoutSecond $duration -listOfAtomics $schedule
    if($null -ne $cleanup){
        Invoke-AtomicRunner -Session $sess -listOfAtomics $schedule -Cleanup
    }
    Disconnect-PSSession $sess.Id
    Remove-PSSession $sess.Id
}else{
    Invoke-AtomicRunner -listOfAtomics $schedule -CheckPrereqs
    Invoke-AtomicRunner -TimeoutSecond $duration -listOfAtomics $schedule
    if($null -ne $cleanup){
        Invoke-AtomicRunner -listOfAtomics $schedule -Cleanup    
    }
}
"Done with pwsh schedule script"
