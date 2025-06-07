# SNMP Printer Supplies
Use this on macOS or Linux web server to display the printer toner levels and other supply levels on an intranet web page.

## Example usage
```
$printer1 = check_printer_supplies( '192.168.0.101' );
```
Or to use one less request, specify the number of supply types, where supply types are toner colours, drums, transfer kits, fuser kits, etc. A quick way to know the number is to use the above and then count the rows.
```
$printer1 = check_printer_supplies( '192.168.0.101', 2 );
```
Insert the additional CSS in the header:
```
<style>
<?php echo $printer1['style']; ?>
</style>
```
Insert the results table in the body:
```
<?php echo $printer1['html']; ?>
```
# Alternative

To check supply levels from the command line, use the following commands:

## supply types
```
snmpwalk -v 1 -c public -O va 192.168.0.103 SNMPv2-SMI::mib-2.43.11.1.1.6
```

## supply levels
```
snmpwalk -v 1 -c public -O va 192.168.0.103 SNMPv2-SMI::mib-2.43.11.1.1.9
```

The SNMPWALK program is also [downloadable](https://sourceforge.net/projects/net-snmp/files/net-snmp/) for Windows, but I have not tested it.

# Automation

A Python script has been added for automation. This is deployed on `zeus-automate` and symlinked by jeremy at `~/scripts/printers`. It is triggered by user cron daily:

```
# Check printer toner
33 9 * * * python3 /home/jeremy/scripts/printers/snmp-printer-supplies.py --email person1@adhd.org.sa --cc person2@adhd.org.sa
```
