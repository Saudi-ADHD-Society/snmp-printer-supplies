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
