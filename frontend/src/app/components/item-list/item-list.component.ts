import { Component, OnInit } from '@angular/core';
import { Item } from '../../models/item.model';
import { ItemService } from '../../services/item.service';

@Component({
  selector: 'app-item-list',
  templateUrl: './item-list.component.html',
  styleUrls: ['./item-list.component.css']
})
export class ItemListComponent implements OnInit {
  items: Item[] = [];
  loading = false;
  error: string | null = null;

  constructor(private itemService: ItemService) { }

  ngOnInit() {
    this.getItems();
  }

  getItems() {
    this.loading = true;
    this.error = null;
    
    this.itemService.getItems().subscribe({
      next: (data) => {
        this.items = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load items. Please try again later.';
        this.loading = false;
        console.error('Error loading items:', err);
      }
    });
  }
}
